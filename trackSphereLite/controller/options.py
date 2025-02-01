from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from trackSphereLite.controller.auth import login_required
from trackSphereLite.model.db import DataAccess


bp = Blueprint('options', __name__)


@bp.route('/')
@login_required
def index():
    return render_template('application/options.html')
