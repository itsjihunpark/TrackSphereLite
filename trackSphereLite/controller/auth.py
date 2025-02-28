from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, current_app
)
import functools
from werkzeug.security import check_password_hash, generate_password_hash
from trackSphereLite.model.db import DataAccess


bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/signup', methods=('GET', 'POST'))
def signup():
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        password = request.form['password']
        error = None
        
        if not username:
            error = 'Enter Username'
        elif not password:
            error = 'Enter Password'
        elif not name:
            error = 'Enter Name'

        if error is None: 
            db_obj = DataAccess()
            ret = db_obj.insert_new_user(username, generate_password_hash(password), name)
        if not ret:
            flash(error)
        else:
            current_app.logger.info(f"New Golfer {username} signed up")
            return redirect(url_for('auth.signin'))
        
    return render_template('auth/signup.html')

@bp.route('/signin', methods=('GET', 'POST'))
def signin():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        db_obj = DataAccess()
        error = None
        user = db_obj.get_golfer_by_username(username)
        
        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['golfer_id'] = user['golferID']
            current_app.logger.info(f"Golfer {session.get('golfer_id')} signed in")
            return redirect(url_for('index'))
        
        flash(error)

    return render_template('auth/signin.html')

# checks user_id session variable.
# if session variable user_id is already assigned a value
# set request specific object to hold user object
@bp.before_app_request
def load_signed_in_user():
    golfer_id = session.get('golfer_id')
    db_obj = DataAccess()
    if golfer_id is None:
        g.golfer = None
    else:
        g.golfer = db_obj.get_golfer_by_golfer_id(golfer_id)

@bp.route('/logout')
def logout():
    current_app.logger.info(f"User {session.get('golfer_id')} signed out")
    session.clear()
    return redirect(url_for('index'))

# wraps view functions and checks if g.golfer
# is assigned a value.   
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwarg):
        if g.golfer is None:
            return redirect(url_for('auth.signin'))
        return view(**kwarg)
    return wrapped_view

