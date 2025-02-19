from trackSphereLite.model.util import singleton
import numpy as np
import cv2
import time

@singleton
class BinocularCamera:
    
    def __init__(self, config=None):
        self.config = config

        self.setup_camera()
        self.baseline = self.config["stereo_baseline"]
        self.video_player = None

        try:
            from libcamera import Transform
            from picamera2 import Picamera2
            self.camera_slave = Picamera2(1)
            self.camera_master = Picamera2(0)
            
            
            config = self.camera_slave.create_video_configuration({"format":"RGB888", "size":(1440,1080) },raw=None, transform=Transform(hflip=1, vflip=1))
            self.camera_slave.configure(config)
            config = self.camera_master.create_video_configuration({"format":"RGB888", "size":(1440,1080) },raw=None, transform=Transform(hflip=1, vflip=1))
            self.camera_master.configure(config)
            
            self.camera_slave.start()
            self.camera_master.start()
            
            
        except:
            self.video_player= cv2.VideoCapture(0)

    def __iter__(self):
        return self
    
    def __next__(self):
        
        if self.video_player is None:
            frame_right = self.camera_master.capture_array() # master captures
            frame_left = self.camera_slave.capture_array() #  slave listens and captures next
            frame_left, frame_right = self.undistort_and_rectify_image_pair(frame_left, frame_right)
            return frame_left, frame_right           
            
        else:
            ret, frame = self.video_player.read()
            if ret:
                frame_left, right_frame = self.undistort_and_rectify_image_pair(frame, frame)
                return frame_left, frame_left
        
    def setup_camera(self, mode="fullframe"):
        calibration_values = np.load(self.config['calibration_file'], allow_pickle=True).item()
        self.initialise_undistortion_and_rectification_map(calibration_values)
        self.focal_length_px = calibration_values['Kl'][1][1]

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
