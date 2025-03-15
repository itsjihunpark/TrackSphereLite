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
        results = self.model.predict(frame, conf=0.8, verbose=False, classes=self.config['detection_classes']) 
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
    
if __name__ == "__main__":
    pass

