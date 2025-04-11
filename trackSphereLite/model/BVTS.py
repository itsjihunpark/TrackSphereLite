from trackSphereLite.model.util import singleton
from trackSphereLite.model.BinocularCamera import BinocularCamera
from trackSphereLite.model.ObjectDetector import ObjectDetector
from trackSphereLite.model.FrameProducer import MotionFileredFrameProducer, ReplayFrameProducer
from trackSphereLite.model.Golfball import FlightedGolfball, RollingGolfball
from trackSphereLite.model.db import DataAccess
import json
import cv2
from trackSphereLite.model import cv_util 
from trackSphereLite.model import util
import numpy as np
from trackSphereLite import socket
import base64
import eventlet
import os
import pickle
from datetime import datetime

@singleton
class BVTS:
    
    def __init__(self):
        f = open("./bvts_config/config.json")  
        self.config = json.load(f)
        self.bicam = BinocularCamera()


    def initiate_golf_ball_tracking_algorithm(self, event):
        # phase 1        

        for frame_left, frame_right, ts_left, ts_right in self.bicam:
            if not event.is_set():
                print("CURRENT BACKGROUND THREAD TERMINATED")
                return
            
            ret, buffer = cv2.imencode('.jpg', frame_right)
            frame_right = base64.b64encode(buffer).decode('utf-8')
            socket.emit('frame', frame_right)
            eventlet.sleep(0.001)
       