from flask import (
    request, current_app, g, redirect, url_for
)
from werkzeug.exceptions import abort
from flask_restx import Namespace, Resource, fields
from trackSphereLite.model.db import DataAccess
import time
from trackSphereLite.model.BVTSController import BVTSController

# reference: https://flask-restx.readthedocs.io/en/latest/
api = Namespace('metric_calculation', version="1.0", title="Auth")
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

@api.route('/flighted_trajectory')
class FlightedTrajectoryMetrics(Resource):
    
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

@api.route('/set_monitor_mode')
class SetMonitorMode(Resource):
     def post(self):
        if g.golfer:
            req_data = request.get_json()
            selected_club = req_data.get("selected_club")
            save_metric = req_data.get("save_metric")
            
            time.sleep(10)
            return {"correct_position": True}
        else:
            return redirect(url_for('auth.signin'))

@api.route('/set_record_mode')
class SetRecordMode(Resource):
     def post(self):
        if g.golfer:
            req_data = request.get_json("")
            time.sleep(10)
            return {"recording_complete": True}
        else:
            return redirect(url_for('auth.signin'))
        
#util
def string_list_to_list(string_list):
    return tuple(map(int, (string_list.split(","))))

