from trackSphereLite.model.util import singleton
from trackSphereLite.model.BinocularCamera import BinocularCamera
from trackSphereLite.model.ObjectDetector import ObjectDetector
from trackSphereLite.model.FrameProducer import MotionFileredFrameProducer, ReplayFrameProducer
import json
import cv2
import time
from trackSphereLite.model import cv_util 
import numpy as np
from trackSphereLite import socket
import base64
import eventlet
import glob
import os

@singleton
class BVTSController:
    
    def __init__(self):
        f = open("./bvts_config/config.json")  
        self.config = json.load(f)
        self.bicam = BinocularCamera(config=self.config)
        self.obj_det = ObjectDetector(config=self.config)


    def initiate_golf_ball_tracking_algorithm(self, event):
        # phase 1: verify ball correct position
        # phase 2: start video recording
        # phase 3: read videos and timestamps motion detect area of interest and filter frame with above thresh
        # phase 4: run object detection again on filtered frames with above thresh and get an array of 3d coordinates
        # phase 5: post process these coordinates depending on whether they are flighted or rolling ball
        # phase 6: save post processing (trajectory, speed, distance, timestamp, etc) to persistence layer if save option is selected
        # phase 7: emit results via socket to be displayed on the front end
        # phase 8: re initialise camera pair

        # phase 1        

        prev_det_sucess = []
        roi_x1, roi_y1, roi_x2, roi_y2 = self.bicam.roi  
        release_n_frames=10

        producer = MotionFileredFrameProducer(self.bicam, self.bicam.roi, self.bicam.motion_threshold, release_n_frames=release_n_frames)
        downscale = True if self.bicam.mode=="fullframe" else False
        for frame_left, frame_right, ts_left, ts_right, filter_flag in producer:
            if not event.is_set():
                print("CURRENT BACKGROUND THREAD TERMINATED")
                return
            frame_right_annotated = frame_right.copy()
            cv2.rectangle(frame_right_annotated, (roi_x1, roi_y1), (roi_x2, roi_y2), (0,0,255), 4) # draw roi with negative color (red)
            
            if filter_flag:
                cv2.rectangle(frame_right_annotated, (roi_x1, roi_y1), (roi_x2, roi_y2), (0,255,255), 4) # change rectangle color to neutral color (yelow)
                
                bbox, classes = self.obj_det.infer(frame_right)
                bbox_within_roi = False
                if len(bbox) != 0: # if det success
                    for b, c in zip(bbox, classes):
                        det_x1, det_y1, det_x2, det_y2 =  np.array(b).astype(int)
                        cv2.rectangle(frame_right_annotated, (det_x1, det_y1), (det_x2, det_y2), (0,255,0), 3)  # change rectangle color to show process(orange)
                        cv2.rectangle(frame_right_annotated, (roi_x1, roi_y1), (roi_x2, roi_y2), (0,165,255), 4)
                        bbox_within_roi = cv_util.check_det_within_roi([roi_x1, roi_y1, roi_x2, roi_y2],[det_x1, det_y1, det_x2, det_y2])
                if not bbox_within_roi:
                    prev_det_sucess = []
                else:
                    prev_det_sucess.append(True)
                    last_n_det = len(prev_det_sucess) 
                    
                    cv2.rectangle(frame_right_annotated, (roi_x1, roi_y1), (roi_x2, roi_y2), (0,255,0), 3)  # change rectangle color to positive color(green)
                          
                    if last_n_det > release_n_frames:
                        # correct position determined since the object has been within the roi 
                        # for release_n_frame of frame
                        break
            
            if downscale:
                frame_right_annotated = cv2.resize(frame_right_annotated, (0, 0), fx=0.5, fy=0.5)
            
            # applying image mirroring effect for better ux
            frame_right_annotated = cv2.flip(frame_right_annotated,1)


            ret, buffer = cv2.imencode('.jpg', frame_right_annotated)
            frame_right_annotated = base64.b64encode(buffer).decode('utf-8')
            socket.emit('frame', frame_right_annotated)
            eventlet.sleep(0.001)
                     
        socket.emit('initial_ball_position_verification', {"message": "verified"})
        eventlet.sleep(0)
        print("Ball correct position detected")

        # phase 2  
        dest_sink, dest_source, dest_sink_ts, dest_source_ts = self.bicam.record_synchronised_video()
        print("Recording success")
        eventlet.sleep(0)
        socket.emit('recording_status', {"message": "success"})
        eventlet.sleep(0)

        # phase 3
        right_video_producer = cv2.VideoCapture(dest_sink)
        left_video_producer = cv2.VideoCapture(dest_source)

        right_pts =open(dest_sink_ts, "r")
        left_pts = open(dest_source_ts, "r")

        # if video was recorded on "croppedframe" mode then source captures one additional frame
        # so the first frame needs to be discarded, first pts must be discarded
        first_left_ts = 0
        if self.bicam.mode == "croppedframe":
            ret, frame = left_video_producer.read() 
            left_pts.readline()
            left_pts = left_pts.readlines()
            first_left_ts = float(left_pts[0].strip().split("=")[1])
        
        left_pts = iter(left_pts)
        right_pts= iter(right_pts.readlines())
        
        producer = ReplayFrameProducer(left_video_producer, right_video_producer, left_pts, right_pts, first_left_ts)
        n_seconds_to_track_after_motion_det = self.config['camera_sensor_setting_values'][self.bicam.mode]['n_seconds_to_track_after_motion_det']
        fps = self.config['camera_sensor_setting_values'][self.bicam.mode]['fps']
        release_n_frames = int(fps * n_seconds_to_track_after_motion_det)
        
        # phase 4
        producer = MotionFileredFrameProducer(producer, self.bicam.roi, self.bicam.motion_threshold, release_n_frames=release_n_frames)
        motion_count = 0
        for frame_left, frame_right, ts_left, ts_right, filter_flag in producer:
            if filter_flag:
                motion_count+=1
            eventlet.sleep(0.001)

        print(f"motion_count: {motion_count}")

        socket.emit('analysis_result', {"results": "Some results to go here which will feed the plotting displaying data"})       
        eventlet.sleep(0)
        # phase 8
        """
        for frame_left, frame_right, ts_left, ts_right in self.bicam:
            if count == 100:
                break
            bbox_left, classes = self.obj_det.infer(frame_left)

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


    # need to move them to cv_util
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
