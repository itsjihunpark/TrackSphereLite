from trackSphereLite.model.util import singleton
import numpy as np
import cv2
import time
from libcamera import Transform
from picamera2 import Picamera2
from datetime import datetime
import os
import subprocess
import eventlet

@singleton
class BinocularCamera:
    
    def __init__(self, config=None):
        self.config = config
        self.baseline = self.config["stereo_baseline"]

        try:
            self.initialise_camera()
        except:
            print("something has gone wrong with the camera") # make better exception message
 

    def __iter__(self):
        return self
    

    def __next__(self):        
        frame_right = self.camera_master.capture_array() # master captures
        frame_left = self.camera_slave.capture_array() #  slave listens and captures next
        ts_right = self.camera_master.capture_metadata()['SensorTimestamp']
        ts_left = self.camera_slave.capture_metadata()['SensorTimestamp']

        frame_left, frame_right = self.undistort_and_rectify_image_pair(frame_left, frame_right)
        return frame_left, frame_right, ts_left, ts_right           


    def initialise_camera(self):
        self.camera_slave = Picamera2(1)
        self.camera_master = Picamera2(0)


    def stop_camera_pair(self):
        self.camera_slave.stop()
        self.camera_master.stop()
    

    def release_camera_pair(self):
        self.camera_slave.close()
        self.camera_master.close()
        

    def start_camera_pair(self):
        self.camera_slave.start()
        self.camera_master.start()


    def setup_camera(self, mode="fullframe"):
        self.mode = mode
        self.roi = self.config['camera_sensor_setting_values'][self.mode]['initial_ball_position_roi']
        self.motion_threshold = self.config['camera_sensor_setting_values'][self.mode]['motion_threshold']

        # read correct camera_calibration_files depending on the mode
        camera_config = self.config['camera_calibration_files'][self.mode]
        calibration_values = np.load(camera_config['calibration_file'], allow_pickle=True).item()
        
        

        self.initialise_undistortion_and_rectification_map(calibration_values)
        self.focal_length_px = calibration_values['Kl'][1][1]
        self.optical_center_x = calibration_values['Kl'][0][2]
        self.optical_center_y = calibration_values['Kl'][1][2]
        
        # create camera_config depending on the mode
        self.stop_camera_pair()
        self.image_size = calibration_values['img_size']
        config = self.camera_slave.create_video_configuration({"format":"RGB888", "size": self.image_size },raw=None, transform=Transform(hflip=1, vflip=1))
        self.camera_slave.configure(config)
        self.camera_slave.controls.ExposureTime = 2500
        config = self.camera_master.create_video_configuration({"format":"RGB888", "size": self.image_size },raw=None, transform=Transform(hflip=1, vflip=1))
        self.camera_master.configure(config)
        self.camera_master.controls.ExposureTime = 2500


    def undistort_and_rectify_image_pair(self, left_frame, right_frame):
        left_img_undistorted_and_rectified = cv2.remap(left_frame, self.xmap1, self.ymap1, cv2.INTER_LINEAR)
        right_img_undistorted_and_rectified = cv2.remap(right_frame, self.xmap2, self.ymap2, cv2.INTER_LINEAR)

        return left_img_undistorted_and_rectified, right_img_undistorted_and_rectified


    def initialise_undistortion_and_rectification_map(self, calibration_values):
        Kl, Dl, Kr, Dr, R, T, img_size = calibration_values['Kl'], calibration_values['Dl'], \
                                        calibration_values['Kr'], calibration_values['Dr'], \
                                        calibration_values['R'], calibration_values['T'], \
                                        calibration_values['img_size']
        
        R1, R2, P1, P2, Q, validRoi1, validRoi2 = cv2.stereoRectify(Kl, Dl, Kr, Dr, img_size, R, T)
        self.xmap1, self.ymap1 = cv2.initUndistortRectifyMap(Kl, Dl, R1, P1, img_size, cv2.CV_32FC1)
        self.xmap2, self.ymap2 = cv2.initUndistortRectifyMap(Kr, Dr, R2, P2, img_size, cv2.CV_32FC1)


    def record_synchronised_video(self):
        temporary_video_record_directory = self.config['temporary_video_record_directory']
        now = datetime.now()
        DATETIME = now.strftime("%Y%m%d_t_%H%M%S")
        dest_sink = str(os.path.join(temporary_video_record_directory,f"{DATETIME}_sink.mp4"))
        dest_source = str(os.path.join(temporary_video_record_directory,f"{DATETIME}_source.mp4"))
        dest_sink_ts = dest_sink.replace(".mp4", ".txt")
        dest_source_ts = dest_source.replace(".mp4", ".txt")

        sensor_config = self.config['camera_sensor_setting_values'][self.mode]
        sensor_width = sensor_config['crop_width']
        sensor_height = sensor_config['crop_height']
        img_width = self.image_size[0]
        img_height = self.image_size[1]
        shutter_exposure_time = sensor_config['exposure_time']
        fps = sensor_config['fps']
        # For cropped high fps mode, the total_record_time_in_seconds is 20 (strangely changes when I reboot though...hm..) 
        num_frame_to_capture_source =  sensor_config['total_record_time_in_seconds']*fps 
        num_frame_to_capture_sink = num_frame_to_capture_source - 1
        self.stop_camera_pair()
        self.release_camera_pair()

        time.sleep(2)
        eventlet.sleep(0)
        print("CAMERA RELEASED")
        """
            The below workaround was because the Picamera2 library (python wrapper for *libcamera)
            did not include the functionality:
            
            1. Changing camera sensor crop size to handle higher framerate
            2. Synchronous high speed video recording via hardware sync rather than software sync
            See the *thread conversation with a raspberry pi engineer: 
        
            For this reason, a system call to run a shell script which executes the above 2 usecases via 
            the libcamera software directly was used as a workaround to enable high fps synchronous recording.
            This however, assumes perfect execution of the shell script when called and failure wihthin the shell 
            script could propagate to failure of this software.


            For recording larger image at a lower framerate, hardware sync was deemed not neccessory. Hence the
            Picamera2 API was used within the python code.
            
            
            libcamera: https://en.wikipedia.org/wiki/Libcamera
            libcamera-official-repo: https://git.linuxtv.org/libcamera.git/
            V4L: https://en.wikipedia.org/wiki/Video4Linux
            Picamera2 library: https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf
            RPiCam repo: https://github.com/raspberrypi/rpicam-apps
            
            *libcamera: an open source project (continuation of V4L - Video4Linux) which provides library 
            for image signal processors and embedded cameras on linux os on Arm processors. libcamera 
            provides a C++ API that configures the camera, then allows applications to request image frames. 
            The Raspberry Pi OS distribution uses a fork to control updates (https://github.com/raspberrypi/libcamera)

            *thread converstion: https://forums.raspberrypi.com/viewtopic.php?p=2295119#p2295119
            
            
        """
        # workaround to handle camera sensor size cropping to reduce image size and increase framerate
        if self.mode == "croppedframe": 
            sh_script = ['sh', './util/record_video_both.sh']
            inputs = [
                    str(sensor_width), str(sensor_height), 
                    str(img_width), str(img_height), 
                    str(fps), str(shutter_exposure_time), 
                    str(num_frame_to_capture_source), 
                    str(num_frame_to_capture_sink),
                    dest_sink, dest_source,
                    dest_sink_ts, dest_source_ts
                    ]  
            
            command = sh_script + inputs
            print(sh_script + inputs)
            print("SUBPROCESS TO RECORD CALLED")
            result = subprocess.call(command)
            
        else:
            self.initialise_camera()
            self.camera_slave.controls.FrameRate = fps
            self.camera_master.controls.FrameRate = fps
            self.camera_slave.controls.ExposureTime = shutter_exposure_time
            self.camera_master.controls.ExposureTime = shutter_exposure_time

            left_config = self.camera_slave.create_video_configuration({"format":"RGB888", "size":(img_width, img_height) },raw=None)
            right_config = self.camera_master.create_video_configuration({"format":"RGB888", "size":(img_width, img_height) },raw=None)
            self.camera_slave.configure(left_config) 
            self.camera_master.configure(right_config) 

            ##SETTING UP CV2 VIDEO SAVING MECHANISM##
            
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            source = cv2.VideoWriter(dest_source, fourcc, fps, (img_width, img_height)) 
            sink = cv2.VideoWriter(dest_sink, fourcc, fps, (img_width, img_height))

            source_ts = []
            sink_ts = []

            self.camera_slave.start()
            self.camera_master.start()
       
            for i in range(0, num_frame_to_capture_source):
                frame1 = self.camera_master.capture_array()
                frame2 = self.camera_slave.capture_array()
        
                ts1 = self.camera_master.capture_metadata()['SensorTimestamp'] / 1e9        
                ts2 = self.camera_slave.capture_metadata()['SensorTimestamp'] / 1e9
        
                sink.write(frame1)
                source.write(frame2)
        
                sink_ts.append(ts1)
                source_ts.append(ts2)
                eventlet.sleep(0.001)

            sink.release()
            source.release()
            with open(dest_source_ts, "w") as f:
                for line in source_ts:
                    f.write(f"pts_time={line}\n")
            with open(dest_sink_ts, "w") as f:
                for line in sink_ts:
                    f.write(f"pts_time={line}\n") 

            self.stop_camera_pair()
            self.release_camera_pair()  
        
        eventlet.sleep(0)
        print("RE INITIALISING CAMERA")
        self.initialise_camera()

        return dest_sink, dest_source, dest_sink_ts, dest_source_ts 



if __name__ == "__main__":
    bicam = BinocularCamera()
    for frame in bicam:
        cv2.imshow("frame", frame)       
        cv2.waitKey(0)
