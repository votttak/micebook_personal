import functools
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from urllib.parse import quote_plus as urlquote
from . import db, Users
from .external_communications import check_irats_credentials

bp = Blueprint('auth', __name__, url_prefix='/auth')



# db.create_all(app=create_app())
# db.session.commit()

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif Users.query.filter(Users.username==username).first() is not None:
            error = 'User {} is already registered.'.format(username)

        if error:
            flash(error)

        else:
            # names = check__credentials(username, password)
            names = check_irats_credentials(username, password)
            if names is None:
                flash('These credentials are not recognized by Irats. Please make sure you are using the same exact username and password to register or wait for Irats to be back online.')
            else:
                new_user =  Users(username=username, password=generate_password_hash(password), full_name=names[1]+' '+names[0])
                db.session.add(new_user)
                db.session.commit()
                return redirect(url_for('auth.login'))


    return render_template('auth/register.html')


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        error = None
        user = Users.query.filter(Users.username==username).first()

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user.password, password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user.id
            return redirect(url_for('index'))

        flash(error)

    return render_template('auth/login.html')

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = Users.query.filter(Users.id==user_id).first()

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
            
        return view(**kwargs)

    return wrapped_view