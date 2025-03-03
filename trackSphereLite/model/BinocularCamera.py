from trackSphereLite.model.util import singleton
import numpy as np
import cv2
import time
from libcamera import Transform
from picamera2 import Picamera2
from datetime import datetime
import os
import subprocess

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
        self.roi = self.config['camera_sensor_setting_values'][mode]['initial_ball_position_roi']
        self.mode = mode
        # read correct camera_calibration_files depending on the mode
        camera_config = self.config['camera_calibration_files'][self.mode]
        calibration_values = np.load(camera_config['calibration_file'], allow_pickle=True).item()
        self.initialise_undistortion_and_rectification_map(calibration_values)
        self.focal_length_px = calibration_values['Kl'][1][1]

        # create camera_config depending on the mode
        self.stop_camera_pair()
        self.image_size = calibration_values['img_size']
        config = self.camera_slave.create_video_configuration({"format":"RGB888", "size": self.image_size },raw=None, transform=Transform(hflip=1, vflip=1))
        self.camera_slave.configure(config)
        config = self.camera_master.create_video_configuration({"format":"RGB888", "size": self.image_size },raw=None, transform=Transform(hflip=1, vflip=1))
        self.camera_master.configure(config)


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
        self.stop_camera_pair()
        self.release_camera_pair()
        subprocess.call(['libcamera-hello', '--list-camera'])

        print("Starting video capture")
        temporary_video_record_directory = self.config['temporary_video_record_directory']
        sensor_config = self.config['camera_sensor_setting_values'][self.mode]
        
        sensor_width = sensor_config['crop_width']
        sensor_height = sensor_config['crop_height']
        img_width = self.image_size[0]
        img_height = self.image_size[1]
        shutter_exposure_time = sensor_config['exposure_time']
        fps = sensor_config['fps']
        num_frame_to_capture_source =  sensor_config['total_record_time_in_seconds']*fps
        num_frame_to_capture_sink = num_frame_to_capture_source - 1
        
        now = datetime.now()
        DATETIME = now.strftime("%Y%m%d_t_%H%M%S")

        dest_sink = str(os.path.join(temporary_video_record_directory,f"{DATETIME}_sink.mkv"))
        dest_source = str(os.path.join(temporary_video_record_directory,f"{DATETIME}_source.mkv"))
        dest_sink_ts = str(os.path.join(temporary_video_record_directory,f"{DATETIME}_sink.txt"))
        dest_source_ts = str(os.path.join(temporary_video_record_directory,f"{DATETIME}_source.txt"))

        sh_script = ['sh', './bvts_config/record_video_both.sh']
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
        time.sleep(2)
        print(sh_script + inputs)
        result = subprocess.call(command)
        return result
    
if __name__ == "__main__":
    bicam = BinocularCamera()
    for frame in bicam:
        cv2.imshow("frame", frame)       
        cv2.waitKey(0)
