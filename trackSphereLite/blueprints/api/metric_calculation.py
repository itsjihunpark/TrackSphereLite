from flask import (
    request, current_app, g, redirect, url_for, session
)
from werkzeug.exceptions import abort
from flask_restx import Namespace, Resource, fields
from trackSphereLite.model.db import DataAccess
import time
from trackSphereLite.model.BVTS import BVTSController
import json
import os
import pickle

# reference: https://flask-restx.readthedocs.io/en/latest/
api = Namespace('metric_calculation', version="1.0", title="metrics")
metric_id_list_model = api.model('metric_id_list_model', {"metric_id_list": fields.String(required=True, min_length=1, max_length=100)})

@api.route('/metrics')
class AllMetrics(Resource):
   
    def get(self):
        if g.golfer:
            db_access = DataAccess()
            golfball_list = db_access.get_all_golf_swing_metrics_by_golfer_id(g.golfer['golferID'])
            golfball_dict_list = [golfball.__dict__ for golfball in golfball_list]
            return golfball_dict_list

        else:
            return redirect(url_for('auth.signin'))

    @api.expect(metric_id_list_model, validate=True)
    def post(self):
        if g.golfer:
            req_data = request.get_json()
            metric_id_list = req_data.get("metric_id_list")
            metric_id_list = string_list_to_list(metric_id_list)
            db_access = DataAccess()
            golfball_list = db_access.get_all_golf_swing_metrics_by_golfballID(metric_id_list)
            golfball_dict_list = [golfball.__dict__ for golfball in golfball_list]
            return golfball_dict_list
        else:
            return redirect(url_for('auth.signin'))

@api.route('/trajectory')
class TrajectoryMetrics(Resource):
    
    @api.expect(metric_id_list_model, validate=True)
    def post(self):
        if g.golfer:
            req_data = request.get_json()
            metric_id_list = req_data.get("metric_id_list")
            metric_id_list = string_list_to_list(metric_id_list)
            current_app.logger.info(f"REQUESTING TRAJECTORY FOR {metric_id_list}", )
            db_access = DataAccess()
            golfball_list = db_access.get_all_golf_swing_metrics_by_golfballID(metric_id_list)
            trajectory_plots = []
            for golfball in golfball_list:
                x, y, z = golfball.get_golfball_motion_properties(get_trajectory=True)
         
                trajectory = {
                    "x": x,
                    "y": y,
                    "z": z
                }
                trajectory_plots.append(trajectory)
                
            return trajectory_plots
        else:
            return redirect(url_for('auth.signin'))


@api.route('/single_metric_from_pickle')
class SingleMetricFromPickle(Resource):
   
    def get(self):
        if g.golfer:
            f = open("./bvts_config/config.json")  
            config = json.load(f)
            temporary_results_pkl_path = os.path.join(config['temporary_video_record_directory'],"golfball.pkl")
            
            if os.path.exists(temporary_results_pkl_path):
                with open(temporary_results_pkl_path, "rb") as res:
                    result = pickle.load(res)
                    
                os.remove(temporary_results_pkl_path)                

                golfball = result['golfball']
                if result['save_result']:
                    # call to db to insert
                    db_access = DataAccess()
                    golfball_id = db_access.insert_golfball(golfball, session.get('golfer_id'))
                    print(golfball_id)

                metrics = golfball.__dict__ 
                x, y, z = golfball.get_golfball_motion_properties(get_trajectory=True)
                trajectory = {
                    "x": x,
                    "y": y,
                    "z": z
                }
                return {"golfball": {
                    "metric": [metrics],
                    "trajectory": [trajectory]
                }}
            else:
                return{"golfball": None}
        else:
            return redirect(url_for('auth.signin'))

@api.route('/delete_metric')
class DeleteMetric(Resource):
    def post(self):
        if g.golfer:
            req_data = request.get_json()
            metric_id = req_data.get("metric_id")
            db_access = DataAccess()

            # retrieve golf ball that is going to be deleted to get video path
            golfball_list = db_access.get_all_golf_swing_metrics_by_golfballID([metric_id])
            f = open("./bvts_config/config.json")  
            config = json.load(f)
            video_path = os.path.join(config['video_save_directory'], golfball_list[0].replaypath)
            # delete video if exists
            if os.path.exists(video_path):
                print(f"deleting {video_path}")
                second_video = video_path.replace("sink", "source")
                os.remove(video_path)
                os.remove(second_video)
            # delete from db
            db_access.delete_golfball_metric_by_id(metric_id)
        else:
            return redirect(url_for('auth.signin'))
#util
def string_list_to_list(string_list):
    return tuple(map(int, (string_list.split(","))))

