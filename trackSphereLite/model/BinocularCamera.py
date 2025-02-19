from trackSphereLite.model.util import singleton
import numpy as np
import cv2
import time
from libcamera import Transform
from picamera2 import Picamera2

@singleton
class BinocularCamera:
    
    def __init__(self, config=None):
        self.config = config
        self.baseline = self.config["stereo_baseline"]

        try:
            self.camera_slave = Picamera2(1)
            self.camera_master = Picamera2(0)
            self.setup_camera()         
        except:
            print("something has gone wrong with the camera") # make better exception message
 
    def __iter__(self):
        return self
    
    def __next__(self):        
        frame_right = self.camera_master.capture_array() # master captures
        frame_left = self.camera_slave.capture_array() #  slave listens and captures next
        frame_left, frame_right = self.undistort_and_rectify_image_pair(frame_left, frame_right)
        return frame_left, frame_right           

        
    def setup_camera(self, mode="fullframe"):

        # read correct camera_config_files depending on the mode
        camera_config = self.config['camera_config_files'][mode]
        calibration_values = np.load(camera_config['calibration_file'], allow_pickle=True).item()
        self.initialise_undistortion_and_rectification_map(calibration_values)
        self.focal_length_px = calibration_values['Kl'][1][1]

        # create camera_config depending on the mode
        self.camera_slave.stop()
        self.camera_master.stop()

        config = self.camera_slave.create_video_configuration({"format":"RGB888", "size":(1440,1080) },raw=None, transform=Transform(hflip=1, vflip=1))
        self.camera_slave.configure(config)
        config = self.camera_master.create_video_configuration({"format":"RGB888", "size":(1440,1080) },raw=None, transform=Transform(hflip=1, vflip=1))
        self.camera_master.configure(config)
        
        self.camera_slave.start()
        self.camera_master.start()

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


if __name__ == "__main__":
    bicam = BinocularCamera()
    for frame in bicam:
        cv2.imshow("frame", frame)       
        cv2.waitKey(0)
