from trackSphereLite.model.util import singleton
from trackSphereLite.model.BinocularCamera import BinocularCamera
from trackSphereLite.model.ObjectDetector import ObjectDetector
from trackSphereLite.model.MotionFilter import MotionFiler
import json
import cv2
import time
from trackSphereLite.model import cv_util 
import numpy as np
from trackSphereLite import socket
import base64
import eventlet
import subprocess

@singleton
class BVTSController:
    
    def __init__(self):
        f = open("./bvts_config/config.json")  
        self.config = json.load(f)
        self.bicam = BinocularCamera(config=self.config)
        self.obj_det = ObjectDetector(config=self.config)

    def initiate_golf_ball_tracking_algorithm(self):
        # phase 1: detect ball correct position
        # phase 2: start video recording
        # phase 3: motion detect area of interest and filter frame with above thresh
        # phase 4: run object detection again on filtered frames with above thresh and get an array of 3d coordinates
        # phase 5: post process these coordinates depending on whether they are flighted or rolling ball
        # phase 6: save post processing (trajectory, speed, distance, timestamp, etc) to persistence layer if save option is selected
        # phase 7: emit results via socket to be displayed on the front end
        # phase 8: re initialise camera pair

        count = 0 #simulating correct ball position detection and end of first phase
        # phase 1
        top_left, bottom_right = self.bicam.roi
        for frame_left, frame_right, ts_left, ts_right, filter_flag in MotionFiler(self.bicam, self.bicam.roi, self.bicam.motion_threshold):
            
            """
            for frame_left, frame_right, ts_left, ts_right in self.bicam:
                if count == 100:
                    break
                bbox_left, frame_left = self.obj_det.infer(frame_left)

                if len(bbox_left) == 1 : 
                    
                    bbox_right = self.obj_det.detect_with_template_matching(bbox_left[0], frame_left, frame_right)
                    
                    centroid_left = cv_util.compute_centroid(bbox_left[0])
                    centroid_right = cv_util.compute_centroid(bbox_right) 
                    
                    cv2.circle(frame_left, centroid_left, 4, (0, 0, 255), 2, 2)
                    
                    x, y, z = self.triangulate(centroid_left, centroid_right)
                    
                    x_diff = centroid_left[0]-centroid_right[0]
                    y_diff = centroid_left[1]-centroid_right[1]             
        
                    left, top, right, bottom = bbox_right
                    cv2.rectangle(frame_right,(left, top), (right, bottom), (0,0,255), 2)
                    position = f"x: {x}m, y: {y}m, z: {z}m"
                    cv2.putText(frame_right, position, centroid_right, cv2.FONT_HERSHEY_PLAIN, 2, (0,0,255), 2)
                    text = f"right camera pixel disparity x: {x_diff} y: {y_diff}"
                    cv2.putText(frame_right, text, (100,100), cv2.FONT_HERSHEY_PLAIN, 2, (0,0,255), 2)
                    text = f"centroid left: {centroid_left} centroid right: {centroid_right}"
                    cv2.putText(frame_right, text, (100,200), cv2.FONT_HERSHEY_PLAIN, 2, (0,0,255), 2)
                    cv2.circle(frame_right, centroid_right, 4, (0, 0, 255), 2, 2)
                """
            cv2.rectangle(frame_right, tuple(top_left), tuple(bottom_right), (255,255,255), 2)
            cv2.putText(frame_right, str(filter_flag), (100,200), cv2.FONT_HERSHEY_PLAIN, 4, (0,0,255), 2)
            ret, buffer = cv2.imencode('.jpg', frame_right)
            frame_right = base64.b64encode(buffer).decode('utf-8')
            socket.emit('frame', frame_right)
            eventlet.sleep(0.001)
            
            count+=1    
            
        socket.emit('initial_ball_position_verification', {"initial_ball_position_set": "true"})
        eventlet.sleep(1)
        print("Ball correct position detected")
        
        # phase 2  
        ret = self.bicam.record_synchronised_video()
        print(ret)
        print("Recording success")

        eventlet.sleep(1)
        socket.emit('recording_status', {"recording_status": "sucess"})
        
        # phase 3

        # phase 8
        self.bicam.initialise_camera()



    def triangulate(self, centroid_left, centroid_right):
        
        xl, yl = centroid_left
        xr, yr = centroid_right

        disparity = xl-xr

        z = (self.bicam.focal_length_px*self.bicam.baseline)/disparity 
        x = (xl*z)/self.bicam.focal_length_px
        y = (yl*z)/self.bicam.focal_length_px

        return round(x, 3), round(y, 3), round(z,3)
    
    def reconstruct_3d(self, centroid_left, centroid_right):
        xl, yl = centroid_left
        xr, yr = centroid_right

        disparity  = xl-xr
        
        # obtain from disparity and depth relationship from the 6th degree polynomial
        z = (self.bicam.focal_length_px*self.bicam.baseline)/disparity 


        # obtain from depth and px width relationship from the quadratic
        x = (xl*z)/self.bicam.focal_length_px


        # obtain from depth and px height relationship from the quadratic
        y = (yl*z)/self.bicam.focal_length_px

        return round(x, 3), round(y, 3), round(z,3)        
