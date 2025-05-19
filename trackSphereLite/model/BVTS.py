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
        self.bicam = BinocularCamera(config=self.config)
        self.obj_det = ObjectDetector(config=self.config)
        self.target_selection = None
        self.target_3d_coordinates = None
        self.target_3d_coordinates_offset = [None,None,None]

    def initiate_golf_ball_tracking_algorithm(self, event, club, save_result):
        # Phase 1: User inputs golf club type and enters whether to store tracked golf ball 
        # ^ user inputs are passed in as arguments for this method
        # open 3d reconstruction model (polynomial regression model) from pickle file
        socket.on_event('target_selection', self.handle_message)

        reconstruct_3d_reg_model_path = self.config['camera_calibration_files'][self.bicam.mode]['reconstruct_3d_reg_model_file']
        
        with open(reconstruct_3d_reg_model_path, "rb") as model:
            reconstruct_3d_reg_model = pickle.load(model)
        if not self.target_selection:
            self.set_target_coordinates(reconstruct_3d_reg_model, event)
        
        # verify initial correct ball position
        x_origin_ball, y_origin_ball, z_origin_ball = self.verify_initial_ball_position(reconstruct_3d_reg_model, event)
        message ={
                "message": "place club at ready position",
                "distance": "",
            }
        socket.emit('initial_positioning_aid', message)
        eventlet.sleep(0)
        self.verify_initial_club_position(reconstruct_3d_reg_model, event)
        # verify initial correct club position
        socket.emit('initial_ball_position_verification', {"message": "verified"})
        eventlet.sleep(0)
        print("Ball correct position detected")

        self.track_putt(x_origin_ball, y_origin_ball, z_origin_ball, reconstruct_3d_reg_model, save_result, event)
        
    def set_target_coordinates(self, reconstruct_3d_reg_model, event):
        for frame_left, frame_right, ts_left_original, ts_right_original in self.bicam:
            if not event.is_set():
                print("CURRENT BACKGROUND THREAD TERMINATED")
                return
                
            frame_right_annotated = frame_right.copy()            

            self.downscale = 0.3 if self.bicam.mode=="fullframe" else False
            
                
            if self.target_selection:
                self.target_bbox = cv_util.convert_normalised_coordinates_to_pixel(self.target_selection, frame_right_annotated.shape[1], frame_right_annotated.shape[0])  
                r_x1, r_y1, r_x2, r_y2 = self.target_bbox
                # Template match this rectangle of the right frame to the left frame
                l_x1, l_y1, l_x2, l_y2 = self.obj_det.detect_with_template_matching([r_x1, r_y1, r_x2, r_y2], frame_right, frame_left)
                
                                
                # Obtain 3D coordinates of the centre of the target 
                if l_x1 is not None and l_y1 is not None and l_x2 is not None and l_y2 is not None:
                    # Set the outcome to the target coordinates attribute
                    self.target_3d_coordinates = []
                    
                    centroid_left = cv_util.compute_centroid([l_x1, l_y1, l_x2, l_y2])
                    centroid_right = cv_util.compute_centroid([r_x1, r_y1, r_x2, r_y2])

                    x, y, z = cv_util.reconstruct_3d(centroid_left, centroid_right, frame_right.shape[0], reconstruct_3d_reg_model, self.bicam.focal_length_px, self.bicam.optical_center_x, self.bicam.optical_center_y)
                    if z > 5:
                        socket.emit("selected_target", {"message": f"target too far {x,y,z}", "system_ready": False})
                        self.target_selection = None
                    elif z < 2:
                        socket.emit("selected_target", {"message": f"target too close: {x,y,z}", "system_ready": False})
                        self.target_selection = None
                    else:
                        self.target_3d_coordinates = [x.item(), y.item(), z.item()]  
                        socket.emit("selected_target", {"message": f"target selected: {x,y,z}", "system_ready": True})
                        return True    

                    eventlet.sleep(0.01)    
                else:
                    self.target_selection = None
            if self.downscale:
                frame_right_annotated = cv2.resize(frame_right_annotated, (0, 0), fx=self.downscale, fy=self.downscale)
            # applying image mirroring effect for better ux
            frame_right_annotated = cv2.flip(frame_right_annotated,1)

            ret, buffer = cv2.imencode('.jpg', frame_right_annotated)
            frame_right_annotated = base64.b64encode(buffer).decode('utf-8')
            socket.emit('frame', frame_right_annotated)
            eventlet.sleep(0.001)

    def verify_initial_ball_position(self, reconstruct_3d_reg_model, event):
        # verifies ball is within trackable distance
        # verifies ball has been stationary for x number of frames within trackable distance
        prev_det_sucess = []
        roi_x1, roi_y1, roi_x2, roi_y2 = self.bicam.roi  
        check_n_images = 15
        prev_origin_x, prev_origin_y, prev_origin_z = 0,0,0

        for frame_left, frame_right, ts_left_original, ts_right_original in self.bicam:
            if not event.is_set():
                print("CURRENT BACKGROUND THREAD TERMINATED")
                self.clear_temp_results()
                return -1, -1, -1
            frame_right_annotated = frame_right.copy()            

            bbox_right, classes_right = self.obj_det.infer(frame_right)
            bbox_left, classes_left = self.obj_det.infer(frame_left)

            ball_within_trackable_initial_position = False
            ball_stationary = False
            if len(bbox_left) != 0 and len(bbox_right) != 0: # if det success
                for b_left, c_left, b_right, c_right in zip(bbox_left, classes_left ,bbox_right, classes_right):
                    b_left = np.array(b_left).astype(int)
                    b_right = np.array(b_right).astype(int)
                    
                    centroid_left = cv_util.compute_centroid(b_left)
                    centroid_right = cv_util.compute_centroid(b_right)

                    if cv_util.bbox_is_valid(b_left, b_right):
                        # 3D reconstruction here to mm
                        x_original ,y_original ,z_original = cv_util.reconstruct_3d(centroid_left, centroid_right, frame_right.shape[0], reconstruct_3d_reg_model, self.bicam.focal_length_px, self.bicam.optical_center_x, self.bicam.optical_center_y)
                        print(f"Detected object (centroid: {centroid_left}  {centroid_right}) at depth: {z_original}m, x: {x_original}m, y: {y_original}m at left_cam: {ts_left_original} right_cam{ts_right_original}")
                        # 3D reconstruction model end here
                        det_x1, det_y1, det_x2, det_y2 = b_right
                        cv2.rectangle(frame_right_annotated, (det_x1, det_y1), (det_x2, det_y2), (0,255,0), 3) 
                        
                        
                        ball_within_trackable_initial_position = True if z_original>=0.9 and z_original<1.3 else False
                        delta_x = abs(prev_origin_x-x_original) 
                        delta_y = abs(prev_origin_y-y_original) 
                        delta_z = abs(prev_origin_z-z_original) 
                        ball_stationary = True if delta_x<=0.02 and delta_y<=0.02 and delta_z<=0.02 else False
                        prev_origin_x, prev_origin_y, prev_origin_z = x_original ,y_original ,z_original
                        if not ball_within_trackable_initial_position:
                            if z_original<=0.9:
                                message = {
                                    "message": "too close",
                                    "distance": z_original,
                                }
                            if z_original>1.3:
                                message ={
                                    "message": "too far",
                                    "distance": z_original,
                                }
                        else:
                            message = {
                                "message": "correct position",
                                "distance": z_original,
                            }
                        socket.emit('initial_positioning_aid', message)
            
            
            if not ball_within_trackable_initial_position:
                prev_det_sucess = []
            else:
                prev_det_sucess.append(True)
                last_n_det = len(prev_det_sucess) 
                
                if last_n_det > check_n_images and ball_stationary:
                    # correct position determined since the object has been within the roi 
                    # for release_n_frame of frame
                    break
            
            r_x1, r_y1, r_x2, r_y2 = self.target_bbox
            cv2.rectangle(frame_right_annotated, (r_x1, r_y1), (r_x2, r_y2), (0,255,0), 3)

            if self.downscale:
                frame_right_annotated = cv2.resize(frame_right_annotated, (0, 0), fx=self.downscale, fy=self.downscale)
            
            # applying image mirroring effect for better ux
            frame_right_annotated = cv2.flip(frame_right_annotated,1)

            ret, buffer = cv2.imencode('.jpg', frame_right_annotated)
            frame_right_annotated = base64.b64encode(buffer).decode('utf-8')
            socket.emit('frame', frame_right_annotated)
            eventlet.sleep(0.001)

        return x_original, y_original, z_original

    def verify_initial_club_position(self, reconstruct_3d_reg_model, event):
        # verifies that club has been stationary for x amount of time
        prev_det_sucess = []  
        check_n_images = 15
        prev_origin_x, prev_origin_y, prev_origin_z = 0,0,0

        for frame_left, frame_right, ts_left_original, ts_right_original in self.bicam:
            if not event.is_set():
                print("CURRENT BACKGROUND THREAD TERMINATED")
                self.clear_temp_results()
                return -1, -1, -1
            frame_right_annotated = frame_right.copy()            

            corners_right = self.obj_det.detect_with_aruco_pattern(frame_right)
            corners_left  = self.obj_det.detect_with_aruco_pattern(frame_left)
            club_stationary = False
            if len(corners_left) == 4 and len(corners_right) == 4: # if det success
                # 3D reconstruction here to mm
                centroid_left = corners_left[0] 
                centroid_right = corners_right[0]

                x_original ,y_original ,z_original = cv_util.reconstruct_3d(centroid_left, centroid_right, frame_right.shape[0], reconstruct_3d_reg_model, self.bicam.focal_length_px, self.bicam.optical_center_x, self.bicam.optical_center_y)
                print(f"Detected object (centroid: {centroid_left}  {centroid_right}) at depth: {z_original}m, x: {x_original}m, y: {y_original}m at left_cam: {ts_left_original} right_cam{ts_right_original}")
                # 3D reconstruction model end here
                
                cv2.circle(frame_right_annotated, centroid_right, 4, (255, 0, 0), 2, 2)
                
                delta_x = abs(prev_origin_x-x_original) 
                delta_y = abs(prev_origin_y-y_original) 
                delta_z = abs(prev_origin_z-z_original) 
                club_stationary = True if delta_x<=0.02 and delta_y<=0.02 and delta_z<=0.02 else False
                prev_origin_x, prev_origin_y, prev_origin_z = x_original ,y_original ,z_original
                
                if not club_stationary :
                    message ={
                        "message": "place club at ready position",
                        "distance": z_original,
                    }
                else:
                    message = {
                        "message": "correct position",
                        "distance": z_original,
                    }
                socket.emit('initial_positioning_aid', message)
            
            if not club_stationary:
                prev_det_sucess = []
            else:
                prev_det_sucess.append(True)
                last_n_det = len(prev_det_sucess) 
                
                if last_n_det > check_n_images and club_stationary:
                    # correct position determined since the object has been within the roi 
                    # for release_n_frame of frame
                    break
            
            r_x1, r_y1, r_x2, r_y2 = self.target_bbox
            cv2.rectangle(frame_right_annotated, (r_x1, r_y1), (r_x2, r_y2), (0,255,0), 3)

            if self.downscale:
                frame_right_annotated = cv2.resize(frame_right_annotated, (0, 0), fx=self.downscale, fy=self.downscale)
            
            # applying image mirroring effect for better ux
            frame_right_annotated = cv2.flip(frame_right_annotated,1)

            ret, buffer = cv2.imencode('.jpg', frame_right_annotated)
            frame_right_annotated = base64.b64encode(buffer).decode('utf-8')
            socket.emit('frame', frame_right_annotated)
            eventlet.sleep(0.001)

        return x_original, y_original, z_original

    def track_putt(self, x_origin_ball, y_origin_ball, z_origin_ball, reconstruct_3d_reg_model, save_result, event):
        timestamped_3d_positions = { 
            "x":[],
            "y":[],
            "z":[], 
            "timestamp_l": [], 
            "timestamp_r": [] # both timestamp to verify frame sync
            }
        detected_strike = False
        non_det_count = 0
        prev_ts_left = 0
        prev_ts_right = 0
        for frame_left, frame_right, ts_left, ts_right in self.bicam:
            if not event.is_set():
                self.clear_temp_results()
                print("CURRENT BACKGROUND THREAD TERMINATED")
                return False
            
            frame_right_annotated = frame_right.copy()
            bbox_right, classes_right = self.obj_det.infer(frame_right)
            bbox_left, classes_left = self.obj_det.infer(frame_left)

            if len(bbox_left) != 0 and len(bbox_right) != 0: # if det success
                for b_left, c_left, b_right, c_right in zip(bbox_left, classes_left ,bbox_right, classes_right):
                    b_left = np.array(b_left).astype(int)
                    b_right = np.array(b_right).astype(int)
                    
                    centroid_left = cv_util.compute_centroid(b_left)
                    centroid_right = cv_util.compute_centroid(b_right)

                    if cv_util.bbox_is_valid(b_left, b_right):
                        non_det_count=0
                        # 3D reconstruction here to mm
                        x ,y ,z = cv_util.reconstruct_3d(centroid_left, centroid_right, frame_right.shape[0], reconstruct_3d_reg_model, self.bicam.focal_length_px, self.bicam.optical_center_x, self.bicam.optical_center_y)
                        print(f"Detected object (centroid: {centroid_left}  {centroid_right}) at depth: {z}m, x: {x}m, y: {y}m at left_cam: {ts_left} right_cam{ts_right}")
                        # 3D reconstruction model end here
                        
                        # only checks for first movement

                        x_delta = abs(x - x_origin_ball)
                        y_delta = abs(y - y_origin_ball)
                        z_delta = abs(z - z_origin_ball)

                        if detected_strike == False and (x_delta > 0.05 or y_delta > 0.05 or z_delta > 0.05):
                            detected_strike = True
                            x_offset = x_origin_ball
                            y_offset = y_origin_ball
                            z_offset = z_origin_ball             
                            timestamped_3d_positions['x_ball'].append(0)
                            timestamped_3d_positions['y_ball'].append(0)
                            timestamped_3d_positions['z_ball'].append(0)
                            timestamped_3d_positions['timestamp_l'].append(prev_ts_left)
                            timestamped_3d_positions['timestamp_r'].append(prev_ts_right)
                            
                            
                            self.target_3d_coordinates_offset[0] = (self.target_3d_coordinates[0]-x_offset).item()
                            self.target_3d_coordinates_offset[1] = (self.target_3d_coordinates[1]-y_offset).item()
                            self.target_3d_coordinates_offset[2] = (self.target_3d_coordinates[2]-z_offset).item()


                            socket.emit('target_position', {'x': self.target_3d_coordinates_offset[0], 'y': self.target_3d_coordinates_offset[1] , 'z': self.target_3d_coordinates_offset[2]})
                            eventlet.sleep(0.001)
                            socket.emit('analysing', {'x': timestamped_3d_positions['x_ball'][-1], 'y': timestamped_3d_positions['y_ball'][-1], 'z': timestamped_3d_positions['z_ball'][-1]})
                            eventlet.sleep(0.001)
                            
                        if detected_strike:
                            timestamped_3d_positions['x_ball'].append(x-x_offset)
                            timestamped_3d_positions['y_ball'].append(y-y_offset)
                            timestamped_3d_positions['z_ball'].append(z-z_offset)
                            timestamped_3d_positions['timestamp_l'].append(ts_left)
                            timestamped_3d_positions['timestamp_r'].append(ts_right)
                            socket.emit('analysing', {'x': timestamped_3d_positions['x_ball'][-1], 'y': timestamped_3d_positions['y_ball'][-1], 'z': timestamped_3d_positions['z_ball'][-1]})
                            eventlet.sleep(0.001)
                            
                            x_delta = abs(timestamped_3d_positions['x_ball'][-1] - timestamped_3d_positions['x_ball'][-2])
                            y_delta = abs(timestamped_3d_positions['y_ball'][-1] - timestamped_3d_positions['y_ball'][-2])
                            z_delta = abs(timestamped_3d_positions['z_ball'][-1] - timestamped_3d_positions['z_ball'][-2])
                            
                        det_x1, det_y1, det_x2, det_y2 = b_right
                        cv2.rectangle(frame_right_annotated, (det_x1, det_y1), (det_x2, det_y2), (0,255,0), 3)
            else:
                non_det_count +=1
                if detected_strike and non_det_count > 10:
                    break
            if len(timestamped_3d_positions['x'])>10 and (x_delta <= 0.01 and y_delta <= 0.01 and z_delta <= 0.01):
                # if ball position did not change for 2 frames in a row
                break    
            prev_ts_left = ts_left            
            prev_ts_right = ts_right

            r_x1, r_y1, r_x2, r_y2 = self.target_bbox
            cv2.rectangle(frame_right_annotated, (r_x1, r_y1), (r_x2, r_y2), (0,255,0), 3)
            
            # applying image mirroring effect for better ux
            frame_right_annotated = cv2.flip(frame_right_annotated,1)
            if self.downscale:
                frame_right_annotated = cv2.resize(frame_right_annotated, (0, 0), fx=self.downscale, fy=self.downscale)
            ret, buffer = cv2.imencode('.jpg', frame_right_annotated)
            frame_right_annotated = base64.b64encode(buffer).decode('utf-8')
            socket.emit('frame', frame_right_annotated)
            eventlet.sleep(0.001)
        # end of real time analysis


        x = util.array_to_csv(timestamped_3d_positions['x_ball'])
        y = util.array_to_csv(timestamped_3d_positions['z_ball'])  
        z = util.array_to_csv(timestamped_3d_positions['y_ball']) 
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  
        try: 
            delta_time = timestamped_3d_positions['timestamp_l'][2] - timestamped_3d_positions['timestamp_l'][1]
            delta_time = delta_time/1000000000 # convert to seconds
        except:
            delta_time = -1
        golfball = RollingGolfball(None, timestamp, "p", "", x,y,z, delta_time, target_coordinate=self.target_3d_coordinates_offset)
        if golfball:
            if save_result == "on":
                save_result = True
            else:
                save_result = False
        temporary_results_pkl_path = os.path.join(self.config['temporary_video_record_directory'],"golfball.pkl")
        with open(temporary_results_pkl_path, "wb") as res:
            pickle.dump({"golfball": golfball, "save_result": save_result}, res, pickle.HIGHEST_PROTOCOL) # highest protocol version of pickle      

        print("Detected ball stoppage OR NON DETECTION")
        socket.emit("analysis_completed", {"message": "ball stopped"})
        eventlet.sleep(0.01)

        return True

    def clear_temp_results(self):
        
        temp_results = os.listdir(self.config['temporary_video_record_directory'])
        for temp_result in temp_results:
            os.remove(os.path.join(self.config['temporary_video_record_directory'], temp_result))
        print("Removed temporary results")
    
    def handle_message(self, data):
        self.target_selection = data['centre_x'], data['centre_y'], data['w'], data['h']
    
"""
        # Starting key frame capture
        w = int(frame_right.shape[1]/2) if downscale else frame_right.shape[1]
        h = int(frame_right.shape[0]/2) if downscale else frame_right.shape[0]

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        replay_video_path= dest_source.replace("temp", "results") # for debug
        replay_video_1 = cv2.VideoWriter(replay_video_path, fourcc, 10, (w, h))# for debug
        replay_video_path = dest_sink.replace("temp", "results")
        replay_video_2 = cv2.VideoWriter(replay_video_path, fourcc, 10, (w, h))

        first_motion = False
        non_detection = []
        timestamped_3d_positions = { 
            "x":[],
            "y":[],
            "z":[], 
            "timestamp_l": [], 
            "timestamp_r": [] # both timestamp to verify frame sync
            }
        
        for frame_left, frame_right, ts_left, ts_right, filter_flag in producer:
            frame_right_annotated = frame_right.copy()
            frame_left_annotated = frame_left.copy() # for debug

            if filter_flag:
                print("Detected Motion")
                bbox_left, classes_l = self.obj_det.infer(frame_left)
                bbox_right, classes_r = self.obj_det.infer(frame_right)

                if len(bbox_left) == 1 and len(bbox_right)==1:      
                    bbox_l =  np.array(bbox_left[0]).astype(int)
                    bbox_r =  np.array(bbox_right[0]).astype(int)
                    # checking bbox aspect ratios
                    

                    centroid_left = cv_util.compute_centroid(bbox_l)
                    centroid_right = cv_util.compute_centroid(bbox_r)
                    
                    if cv_util.bbox_is_valid(bbox_l, bbox_r):
                        # 3D reconstruction here to mm
                        x ,y ,z = cv_util.reconstruct_3d(centroid_left, centroid_right, frame_right.shape[0], reconstruct_3d_reg_model, self.bicam.focal_length_px, self.bicam.optical_center_x, self.bicam.optical_center_y)
                        print(f"Detected object (centroid: {centroid_left}  {centroid_right}) at depth: {z}m, x: {x}m, y: {y}m at left_cam: {ts_left} right_cam{ts_right}")
                        timestamped_3d_positions['x'].append(x)
                        timestamped_3d_positions['y'].append(y)
                        timestamped_3d_positions['z'].append(z)
                        timestamped_3d_positions['timestamp_l'].append(ts_left)
                        timestamped_3d_positions['timestamp_r'].append(ts_right)
                        
                        # 3D reconstruction model end here
                    else:
                        print("invalid bounding box detected")

                    cv2.circle(frame_left_annotated, centroid_left, 4, (0, 0, 255), 2, 2)
                    cv2.circle(frame_right_annotated, centroid_right, 4, (0, 0, 255), 2, 2)
                    cv2.rectangle(frame_left_annotated, (bbox_l[0], bbox_l[1]), (bbox_l[2], bbox_l[3]), (0,255,0), 3) 
                    cv2.rectangle(frame_right_annotated, (bbox_r[0], bbox_r[1]), (bbox_r[2], bbox_r[3]), (0,255,0), 3) 
                    non_detection.append(False)
                    eventlet.sleep(0.01)
                elif len(bbox_left) > 1 or len(bbox_right) > 1:
                    print("more than 2 balls in view")
                    eventlet.sleep(0.01)
                else:
                    non_detection.append(True)
                    print("Detected no object")
                    if self.bicam.mode == "croppedframe" and len(non_detection)>20 and all(non_detection[-20:]):
                        print("No detection for the past 20 frames. Breaking out from the loop")
                        break              
                    eventlet.sleep(0.01)

                if downscale:
                    frame_left_annotated = cv2.resize(frame_left_annotated, (0, 0), fx=0.5, fy=0.5) # for debug
                    frame_right_annotated = cv2.resize(frame_right_annotated, (0, 0), fx=0.5, fy=0.5)
                
                replay_video_1.write(frame_left_annotated) # for debug
                replay_video_2.write(frame_right_annotated) 
                cv2.waitKey(1)

                first_motion = True
                continue
            
            # Only the first set of motion detected frames will be analysed
            if first_motion:
                print("First set of motion detected frames analysed")
                break

            eventlet.sleep(0.01)

        replay_video_1.release()
        replay_video_2.release()

        temp_list = replay_video_path.split('/')[0:-1]
        temp_list.append("temp.mp4")
        temp_path = "/".join(temp_list)

        os.system(f"ffmpeg -i {replay_video_path} -vcodec libx264 -f mp4 {temp_path}")
        os.system(f"rm {replay_video_path}")
        os.system(f"mv {temp_path} {replay_video_path}")

        # removing temporary video
        os.remove(dest_sink)
        os.remove(dest_sink_ts)
        os.remove(dest_source)
        os.remove(dest_source_ts)
        print("Removed temporary video")

        # Phase 5
        # Instantiating golfball
        # Saving results using pickle temporarily.
        golfball = None
        replay_video_path = replay_video_path.split("/")[-1]

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")        
        if club == "p":
            x = util.array_to_csv(timestamped_3d_positions['x'])
            y = util.array_to_csv(timestamped_3d_positions['z'])  
            z = util.array_to_csv(timestamped_3d_positions['y']) 
            delta_time = timestamped_3d_positions['timestamp_l'][-1] - timestamped_3d_positions['timestamp_l'][0]
            golfball = RollingGolfball(None, timestamp, club, replay_video_path, x,y,z, delta_time)
        else:
            velocity_x, velocity_y, velocity_z = cv_util.obtain_velocity_in_meters_per_second(timestamped_3d_positions)
            if velocity_x <= 0 and velocity_y <= 0 and velocity_z == 0:
                return
            print(f"vel_x {velocity_x} vel_y {velocity_y} vel_z {velocity_z}")
            # had to reorder x,y,z since camera coordinate system and final plot coordinate system is different
            golfball = FlightedGolfball(None, timestamp, club, replay_video_path, velocity_x, velocity_z, velocity_y) 
        
        if golfball:
            if save_result == "on":
                save_result = True
            else:
                save_result = False

            temporary_results_pkl_path = os.path.join(self.config['temporary_video_record_directory'],"golfball.pkl")
            with open(temporary_results_pkl_path, "wb") as res:
                pickle.dump({"golfball": golfball, "save_result": save_result}, res, pickle.HIGHEST_PROTOCOL) # highest protocol version of pickle
            

        socket.emit('analysis_status', {"message": "analysis complete"})       
        eventlet.sleep(0)
        """