import cv2
from trackSphereLite.model.BinocularCamera import BinocularCamera
import json

class ReplayFrameProducer:

    def __init__(self, left_video_producer, right_video_producer, left_pts, right_pts, first_left_ts, bicam=None):
        self.left_video_producer = left_video_producer
        self.right_video_producer = right_video_producer
        self.left_pts = left_pts
        self.right_pts = right_pts
        self.first_left_ts = first_left_ts

        if bicam:
            self.bicam = bicam
        else:
            self.bicam = BinocularCamera()

    def __iter__(self):
        return self
    

    def __next__(self):           
        ret, frame_left = self.left_video_producer.read() 
        ret, frame_right = self.right_video_producer.read()
    
        ts_left = float(self.convert_pts_string_to_float(next(self.left_pts))) - self.first_left_ts
        ts_right = float(self.convert_pts_string_to_float(next(self.right_pts))) 
        frame_left = cv2.flip(frame_left, -1) 
        frame_right = cv2.flip(frame_right, -1)
        frame_left, frame_right = self.bicam.undistort_and_rectify_image_pair(frame_left, frame_right) 
        
        return frame_left, frame_right, ts_left, ts_right 
        
        
    def convert_pts_string_to_float(self, pts_string):
        return pts_string.strip().split("=")[-1]


class MotionFileredFrameProducer:
    
    def __init__(self, frame_producer, roi, motion_threshold, release_n_frames=10):
        self.roi_x1, self.roi_y1, self.roi_x2, self.roi_y2 = roi

        self.motion_detection_algo = cv2.createBackgroundSubtractorMOG2(detectShadows=False)
        self.release_n_frames = release_n_frames
        self.release_frames = False
        self.frame_producer = frame_producer
        self.motion_thresh = motion_threshold
        self.release_counter = 10


    def __iter__(self):
        return self
    

    def __next__(self):       
         
        frame_left, frame_right, ts_left, ts_right = next(self.frame_producer)
        forground_mask = self.motion_detection_algo.apply(frame_right)
        roi = forground_mask[self.roi_y1:self.roi_y2, self.roi_x1:self.roi_x2]
        contours, hier = cv2.findContours(roi,cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        total_contour_area = self.get_total_contour_area(contours)
        motion =  total_contour_area > self.motion_thresh
        filter_flag = False
        if motion or self.release_frames:
            if motion:
                self.release_frames = False
            if not self.release_frames:
                self.release_counter = self.release_n_frames
                self.release_frames = True

            if self.release_frames:
                if self.release_counter == 0:
                    self.release_frames = False
                    self.release_counter = self.release_n_frames
                self.release_counter-=1
            filter_flag = True

        return frame_left, frame_right, ts_left, ts_right, filter_flag


    def get_total_contour_area(self, contours):
        total_contour_area = 0
        for contour in contours:
            area = cv2.contourArea(contour)
            total_contour_area+=area
        return total_contour_area



    
if __name__ == "__main__":
    motion_filter = MotionFileredFrameProducer()