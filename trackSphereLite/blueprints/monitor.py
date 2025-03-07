from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, Response, current_app
)
from werkzeug.exceptions import abort
from trackSphereLite.blueprints.auth import login_required
from trackSphereLite.model.db import DataAccess
from trackSphereLite.model.BVTS import BVTSController
from trackSphereLite import socket
from threading import Event, Lock


bp = Blueprint('monitor', __name__, url_prefix='/monitor')
thread_event = Event()
thread_lock = Lock()
global thread
thread = None

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
        
        bvts_controller.bicam.stop_camera_pair()

        if club=="unselected" or club=="p":
            bvts_controller.bicam.setup_camera(mode="fullframe")
        else:
            bvts_controller.bicam.setup_camera(mode="croppedframe")
        bvts_controller.bicam.start_camera_pair()
        global thread
        with thread_lock:
            if thread is None:
                print("NO OTHER BACKGROUND THREAD RUNNING")
                thread_event.set()
                thread = socket.start_background_task(bvts_controller.initiate_golf_ball_tracking_algorithm, thread_event)
            else:
                print("BACKGROUND THREAD RUNNING STOPPED")
                thread_event.clear()
                thread.join()
                thread_event.set()
                thread = socket.start_background_task(bvts_controller.initiate_golf_ball_tracking_algorithm, thread_event)
        print(club, save_result)

    return render_template('application/monitor.html', clubs=clubs, selected_club=club, save_result=save_result)
    
    #return render_template('application/monitor.html', clubs=clubs)
