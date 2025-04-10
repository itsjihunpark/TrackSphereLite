from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, current_app
)
from werkzeug.exceptions import abort

from trackSphereLite.blueprints.auth import login_required
from trackSphereLite.model.db import DataAccess


bp = Blueprint('review', __name__, url_prefix='/review')


@bp.route('/')
@login_required
def index():
    return render_template('application/review.html')

@bp.route('/dashboard', methods=('POST',))
@login_required
def dashboard():
    selected_csv = request.form['selected_csv']
    db_access = DataAccess()
    selected_csv_list = tuple(map(int, (selected_csv.split(","))))
    golfballs = db_access.get_all_golf_swing_metrics_by_golfballID(selected_csv_list)
    replaypaths = []
    for golfball in golfballs:
        replaypaths.append(golfball.replaypath)
    
    current_app.logger.info(replaypaths)
    return render_template('application/dashboard.html', selected_csv=selected_csv, replaypaths=replaypaths)
