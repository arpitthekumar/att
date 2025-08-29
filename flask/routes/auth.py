"""Authentication routes blueprint."""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from services_provider import auth, user_service

bp = Blueprint('auth', __name__)

@bp.route('/')
def index():
    if 'user_id' in session:
        if session['role'] == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif session['role'] == 'teacher':
            return redirect(url_for('teacher.dashboard'))
        else:
            # Check if student has face data before redirecting
            face_data_info = user_service.get_face_data_info(session['user_id'])
            if not face_data_info.get('exists', False):
                flash('Please set up your face data for attendance', 'warning')
                return redirect(url_for('student.capture_face'))
            return redirect(url_for('student.dashboard'))
    return render_template('index.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = auth.authenticate(username, password)
        if user:
            auth.login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('auth.index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@bp.route('/logout')
def logout():
    auth.logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('.login'))
