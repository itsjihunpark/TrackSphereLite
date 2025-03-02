from flask import (
    request, current_app, g, redirect, url_for
)
from werkzeug.exceptions import abort
from flask_restx import Namespace, Resource, fields
from trackSphereLite.model.db import DataAccess
import time
from trackSphereLite.model.BVTSController import BVTSController
import subprocess

# reference: https://flask-restx.readthedocs.io/en/latest/
api = Namespace('camera_control', version="1.0", title="metrics")

@api.route('/start_monitor')
class SetMonitorMode(Resource):
     def post(self):
        if g.golfer:
            req_data = request.get_json()
            selected_club = req_data.get("selected_club")
            save_metric = req_data.get("save_metric")
            bvts_controller = BVTSController()
            bvts_controller.bicam.stop_camera_pair()
            bvts_controller.bicam.release_camera_pair()   
            
            subprocess.call(['libcamera-hello', '--list-camera'])
            

            return {"correct_position": True}
        else:
            return redirect(url_for('auth.signin'))

        