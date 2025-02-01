import numpy as np
from ultralytics import YOLO # https://docs.ultralytics.com/tasks/detect/
from ultralytics.utils.plotting import Annotator
from trackSphereLite.model.util import singleton
from flask import current_app


@singleton
class ObjectDetector:
    
    def __init__(self, config=None):

        self.__private_attribute = "secret shh"
        self.config = config
        self.model = YOLO(self.config["detection_model_path"])
        
    def infer(self, frame):
        # https://docs.ultralytics.com/modes/predict/
        results = self.model.predict(frame, conf=0.3, verbose=False, classes=[0]) 
        bbox = []
        for result in results:
            annotator = Annotator(frame)
            
            boxes = result.boxes
            for box in boxes:
                b = box.xyxy[0]  # get box coordinates in (left, top, right, bottom) format
                bbox.append(b)
                c = box.cls
                annotator.box_label(b, self.model.names[int(c)])
               
        frame = annotator.result()
        
        return bbox, frame
    
if __name__ == "__main__":
    pass

