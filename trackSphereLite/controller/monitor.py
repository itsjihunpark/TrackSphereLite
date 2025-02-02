from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, Response, current_app
)
from werkzeug.exceptions import abort
from trackSphereLite.controller.auth import login_required
from trackSphereLite.model.db import DataAccess
from trackSphereLite.model.BVTSController import BVTSController

bp = Blueprint('monitor', __name__, url_prefix='/monitor')


@bp.route('/')
@login_required
def index():
    clubs = ['3i', '4i', '5i', '6i', '7i', '8i' ,'9i', 'pw54', 'pw56', 'pw58', 'd', '3w', 'p'] # can extract to config
    return render_template('application/monitor.html', clubs=clubs)

@bp.route('/acquire_images')
def acquire_images():
    bvts_controller = BVTSController()
    return Response(bvts_controller.start_ball_position_verification(), mimetype="multipart/x-mixed-replace; boundary=frame")

def shutdown_camera(e=None):
    bvts_controller = BVTSController()
    bvts_controller.bicam.camera_master.stop()
    bvts_controller.bicam.camera_slave.stop()
    current_app.logger.info("CAMERA SHUTDOWN COMPLETE")
    
