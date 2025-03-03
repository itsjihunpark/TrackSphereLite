import cv2
class MotionFiler:
    
    def __init__(self, frame_producer, roi, motion_threshold):
        self.roi_top_left = roi[0]
        self.roi_bottom_right= roi[1]
        self.motion_detection_algo = MOG2_subtractor = cv2.createBackgroundSubtractorMOG2(detectShadows=False)
        self.release_n_frames = 10
        self.release_frames = False
        self.frame_producer = frame_producer
        self.motion_thresh = motion_threshold
        self.release_counter = 10

    def __iter__(self):
        return self
    

    def __next__(self):       
         
        frame_left, frame_right, ts_left, ts_right = next(self.frame_producer)
        forground_mask = self.motion_detection_algo.apply(frame_right)
        roi = forground_mask[self.roi_top_left[1]:self.roi_bottom_right[1], self.roi_top_left[0]:self.roi_bottom_right[0]]
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
    motion_filter = MotionFiler()
