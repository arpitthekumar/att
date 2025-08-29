from flask import Blueprint, render_template, request, redirect, url_for, flash
from backend.auth import student_required, track_activity
from services_provider import (
    user_service, class_service, attendance_service,
    dashboard_service
)

bp = Blueprint('student', __name__, url_prefix='/student')

@bp.route('/dashboard')
@student_required
@track_activity('student_dashboard')
def dashboard():
    data = dashboard_service.get_student_dashboard_data(request.user_id)
    
    # Get current user information
    user = user_service.get_user_by_id(request.user_id)
    
    # Get student's class information
    student_classes = class_service.get_user_classes(request.user_id, 'student')
    class_info = student_classes[0] if student_classes else None
    
    # Get face data information including the image
    face_data = user_service.get_face_data_info(request.user_id)
    
    # Create student object with all necessary data
    student = {
        'id': user['id'],
        'student_name': user['name'],
        'name': user['name'],  # Adding name for consistency
        'roll_number': class_info['roll_number'] if class_info else None,
        'class_name': class_info['name'] if class_info else 'Not assigned',
        'face_data': face_data,
        'attendance_data': data
    }
    
    return render_template('student/dashboard.html', 
                         student=student,
                         stats=data['attendance_stats'],
                         attendance_records=data['recent_attendance'])

@bp.route('/attendance')
@student_required
@track_activity('student_attendance')
def attendance():
    # Get current user information
    user = user_service.get_user_by_id(request.user_id)
    
    # Get student's class information
    student_classes = class_service.get_user_classes(request.user_id, 'student')
    class_info = student_classes[0] if student_classes else None
    
    # Create student object with required fields
    student = {
        'id': user['id'],
        'student_name': user['name'],
        'roll_number': class_info['roll_number'] if class_info else None,
        'class_name': class_info['name'] if class_info else 'Not assigned'
    }
    
    # Get attendance records
    attendance_records = attendance_service.get_student_attendance(request.user_id)
    
    return render_template('student/attendance.html', 
                         student=student,
                         records=attendance_records)

@bp.route('/capture_face')
@student_required
@track_activity('student_capture_face')
def capture_face():
    success, message = user_service.capture_user_face(request.user_id)
    if success:
        flash('Face data captured successfully!', 'success')
    else:
        flash(f'Failed to capture face: {message}', 'error')
    return redirect(url_for('.dashboard'))
