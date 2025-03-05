import numpy as np
from ultralytics import YOLO # https://docs.ultralytics.com/tasks/detect/
from trackSphereLite.model.util import singleton
from flask import current_app
import cv2

@singleton
class ObjectDetector:
    
    def __init__(self, config=None):

        self.config = config
        self.model = YOLO(self.config["detection_model_path"], task="detect")
        
    def infer(self, frame):
        
        # https://docs.ultralytics.com/modes/predict/
        results = self.model.predict(frame, conf=0.7, verbose=False, classes=self.config['detection_classes']) 
        bbox = []
        classes = []

        for result in results:
            
            boxes = result.boxes
            for box in boxes:
                b = box.xyxy[0]  # get box coordinates in (left, top, right, bottom) format
                bbox.append(b)
                c = box.cls
                classes.append(c)
        return bbox, classes
    
    def detect_with_template_matching(self, bbox, source_frame, target_frame):
        left, top, right, bottom = bbox

        source_img_gray = cv2.cvtColor(source_frame, cv2.COLOR_BGR2GRAY)
        template = source_img_gray[top.int():bottom.int(), left.int():right.int()]
        target_frame_gray = cv2.cvtColor(target_frame, cv2.COLOR_BGR2GRAY)
        target_scanline = target_frame_gray[top.int(): bottom.int(), :]
        
        w, h = template.shape[::-1]

        res = cv2.matchTemplate(target_scanline,template,cv2.TM_SQDIFF)

        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        top_left = (min_loc[0], int(top))
        bottom_right = (min_loc[0] + w, int(bottom))
    
        bbox = top_left[0], top_left[1], bottom_right[0], bottom_right[1]
        return bbox
    
if __name__ == "__main__":
    pass

