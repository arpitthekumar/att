from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from backend.auth import admin_required, track_activity
from services_provider import (
    user_service, class_service, attendance_service,
    class_request_service, activity_service, dashboard_service
)

bp = Blueprint('admin', __name__, url_prefix='/admin')

@bp.route('/add_user', methods=['GET', 'POST'])
@admin_required
@track_activity('admin_add_user')
def add_user():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        name = request.form['name']
        role = request.form['role']
        
        user_id = user_service.create_user(username, password, email, name, role)
        
        if user_id:
            if role == 'student':
                class_id = request.form.get('class_id')
                roll_number = request.form.get('roll_number')
                face_data = request.form.get('face_data')
                
                if class_id and roll_number:
                    class_service.assign_student_to_class(user_id, int(class_id), roll_number)
                
                if face_data:
                    success, message = user_service.capture_user_face(user_id, 'upload', face_data)
                    if success:
                        flash('User created successfully with face data!', 'success')
                    else:
                        flash(f'User created but face data failed: {message}', 'warning')
                    return redirect(url_for('admin.users'))
            flash('User created successfully!', 'success')
            return redirect(url_for('admin.users'))
        else:
            flash('Failed to create user. Username or email may already exist.', 'error')
    
    classes = class_service.get_all_classes()
    return render_template('admin/add_user.html', classes=classes)

@bp.route('/users')
@admin_required
@track_activity('admin_users')
def users():
    role_filter = request.args.get('role')
    if role_filter:
        users = user_service.get_all_users(role_filter)
    else:
        users = user_service.get_all_users()
    return render_template('admin/users.html', users=users, role_filter=role_filter)

@bp.route('/activity')
@admin_required
@track_activity('admin_activity')
def activity():
    hours = request.args.get('hours', 24, type=int)
    role_filter = request.args.get('role')
    
    activities = activity_service.get_recent_activity(hours, role_filter) if role_filter else activity_service.get_recent_activity(hours)
    active_users = activity_service.get_active_users(hours)
    
    return render_template('admin/activity.html', 
                         activities=activities, 
                         active_users=active_users,
                         hours=hours,
                         role_filter=role_filter)

@bp.route('/requests')
@admin_required
@track_activity('admin_requests')
def requests():
    pending_requests = class_request_service.get_pending_requests()
    return render_template('admin/requests.html', requests=pending_requests)
