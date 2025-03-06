from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort
from trackSphereLite.blueprints.auth import login_required
from trackSphereLite.model.db import DataAccess
from trackSphereLite.blueprints.monitor import thread_event, thread_lock

bp = Blueprint('options', __name__)


@bp.route('/')
@login_required
def index():
    with thread_lock:
        thread_event.clear()
        

    return render_template('application/options.html')
