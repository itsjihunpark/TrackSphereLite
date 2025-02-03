from trackSphereLite.model.util import singleton
from trackSphereLite.model.BinocularCamera import BinocularCamera
from trackSphereLite.model.ObjectDetector import ObjectDetector
import json
import cv2
import time
from trackSphereLite.model import cv_util 
import numpy as np

@singleton
class BVTSController:
    
    def __init__(self):
        f = open("./bvts_config/config.json")  
        self.config = json.load(f)
        self.bicam = BinocularCamera(config=self.config)
        self.obj_det = ObjectDetector(config=self.config)

    
    def start_ball_position_verification(self):
        count = 0
        for frame_left, frame_right in self.bicam:

            bbox_left, frame_left = self.obj_det.infer(frame_left)
            # bbox_right, frame_right = self.obj_det.infer(frame_right)

            if len(bbox_left) == 1 : # and len(bbox_right)==1
                
                bbox_right = self.obj_det.detect_with_template_matching(bbox_left[0], frame_left, frame_right)
                
                centroid_left = cv_util.compute_centroid(bbox_left[0])
                centroid_right = cv_util.compute_centroid(bbox_right) 
                
                
                x, y, z = self.triangulate(centroid_left, centroid_right)
                
                x_diff = centroid_left[0]-centroid_right[0]
                y_diff = centroid_left[1]-centroid_right[1]             
    
                left, top, right, bottom = bbox_right
                cv2.rectangle(frame_right,(left, top), (right, bottom), (0,0,255), 2)
                position = f"x: {x}m, y: {y}m, z: {z}m"
                cv2.putText(frame_right, position, centroid_right, cv2.FONT_HERSHEY_PLAIN, 2, (0,0,255), 2)
                text = f"right camera pixel disparity x: {x_diff} y: {y_diff}"
                cv2.putText(frame_right, text, (100,100), cv2.FONT_HERSHEY_PLAIN, 2, (0,0,255), 2)
                cv2.circle(frame_right, centroid_right, 4, (0, 0, 255), 2, 2)

            ret, buffer = cv2.imencode('.jpg', frame_right)
            frame_right = buffer.tobytes()    

            
            """
            if count == 300 :
                time.sleep(10)
            """

            count += 1

            yield(b'--frame\r\nContent-Type: image/jpeg\r\n\r\n'+frame_right+b'\r\n') 
    
    
    def triangulate(self, centroid_left, centroid_right):
        
        xl, yl = centroid_left
        xr, yr = centroid_right

        horizontal_diff_in_px = xl-xr


        z = (self.bicam.focal_length_px*self.bicam.baseline)/horizontal_diff_in_px
        x = (xl*z)/self.bicam.focal_length_px
        y = (yl*z)/self.bicam.focal_length_px

        return round(x, 3), round(y, 3), round(z,3)
