from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, Response, current_app
)
from werkzeug.exceptions import abort
from trackSphereLite.controller.auth import login_required
from trackSphereLite.model.db import DataAccess
from trackSphereLite.model.BVTSController import BVTSController
from trackSphereLite import socket

bp = Blueprint('monitor', __name__, url_prefix='/monitor')


@bp.route('/', methods=('POST', 'GET'))
@login_required
def index():
    clubs = ['3i', '4i', '5i', '6i', '7i', '8i' ,'9i', 'pw54', 'pw56', 'pw58', 'd', '3w', 'p'] # can extract to config
    
    save_result=None
    club=None
    
    if request.method=="POST":
        club = request.form['club']
        save_result = request.form['save_results']
        
        bvts_controller = BVTSController()
        
        bvts_controller.bicam.release_camera_pair()

        if club=="unselected" or club=="p":
            bvts_controller.bicam.setup_camera(mode="fullframe")
        else:
            bvts_controller.bicam.setup_camera(mode="croppedframe")
        bvts_controller.bicam.start_camera_pair()
        socket.start_background_task(bvts_controller.initiate_golf_ball_tracking_algorithm)
        
        print(club, save_result)

        return render_template('application/monitor.html', clubs=clubs, selected_club=club, save_result=save_result)
    
    return render_template('application/monitor.html', clubs=clubs)
