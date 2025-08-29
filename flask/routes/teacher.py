from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from datetime import datetime, date
import csv
import io
import os

from backend.auth import teacher_required, track_activity
from services_provider import (
    user_service, class_service, attendance_service,
    dashboard_service, attendance_session_service,
    class_request_service
)

bp = Blueprint('teacher', __name__, url_prefix='/teacher')

@bp.route('/dashboard')
@teacher_required
@track_activity('teacher_dashboard')
def dashboard():
    data = dashboard_service.get_teacher_dashboard_data(request.user_id)
    user = user_service.get_user_by_id(request.user_id)
    
    return render_template('teacher/dashboard.html', 
                         classes=data['classes'],
                         today_attendance=data['today_attendance'],
                         session={'name': user['name']})

@bp.route('/attendance/<int:class_id>')
@teacher_required
@track_activity('teacher_attendance')
def attendance(class_id):
    class_data = class_service.get_class_by_id(class_id)
    if not class_data:
        flash('Class not found', 'error')
        return redirect(url_for('.dashboard'))
    
    # Check if teacher is assigned to this class
    teacher_classes = class_service.get_user_classes(request.user_id, 'teacher')
    if not any(c['id'] == class_id for c in teacher_classes):
        flash('You are not assigned to this class', 'error')
        return redirect(url_for('.dashboard'))
    
    today = date.today()
    attendance = attendance_service.get_class_attendance(class_id, today)
    students = class_service.get_class_students(class_id)
    
    # Get or create attendance session for today
    session = attendance_session_service.get_or_create_session(class_id, request.user_id)
    temp_attendance = attendance_session_service.get_temporary_attendance(session['id'])
    unrecognized_faces = attendance_session_service.get_unrecognized_faces(session['id'])

    return render_template('teacher/attendance.html', 
                         class_data=class_data, 
                         students=students, 
                         attendance=attendance,
                         today=today,
                         temp_attendance=temp_attendance,
                         unrecognized_faces=unrecognized_faces,
                         session_id=session['id'])

@bp.route('/attendance/start', methods=['POST'])
@teacher_required
@track_activity('teacher_start_attendance')
def start_attendance():
    class_id = request.form.get('class_id')
    student_id = request.form.get('student_id')
    attendance_type = request.form.get('attendance_type', 'regular')
    remarks = request.form.get('remarks', '')
    
    if not class_id or not student_id:
        return jsonify({'success': False, 'message': 'Missing parameters'})
    
    # Verify teacher is assigned to this class
    teacher_classes = class_service.get_user_classes(request.user_id, 'teacher')
    if not any(c['id'] == int(class_id) for c in teacher_classes):
        return jsonify({'success': False, 'message': 'Not authorized for this class'})
    
    # Check if student is in this class
    students = class_service.get_class_students(int(class_id))
    if not any(s['id'] == int(student_id) for s in students):
        return jsonify({'success': False, 'message': 'Student not in this class'})
    
    # Mark attendance with face recognition
    success, message = attendance_service.mark_attendance_with_face(
        int(student_id), int(class_id), request.user_id, attendance_type, remarks
    )
    
    return jsonify({'success': success, 'message': message})

@bp.route('/reports/<int:class_id>')
@teacher_required
@track_activity('teacher_reports')
def reports(class_id):
    class_data = class_service.get_class_by_id(class_id)
    if not class_data:
        flash('Class not found', 'error')
        return redirect(url_for('.dashboard'))
    
    # Check if teacher is assigned to this class
    teacher_classes = class_service.get_user_classes(request.user_id, 'teacher')
    if not any(c['id'] == class_id for c in teacher_classes):
        flash('You are not assigned to this class', 'error')
        return redirect(url_for('.dashboard'))
    
    students = class_service.get_class_students(class_id)
    
    # Add attendance statistics for each student
    for student in students:
        stats = attendance_service.get_attendance_stats(student['id'], class_id)
        student.update(stats)
    
    return render_template('teacher/reports.html', class_data=class_data, students=students)

@bp.route('/export/<int:class_id>')
@teacher_required
@track_activity('teacher_export')
def export(class_id):
    class_data = class_service.get_class_by_id(class_id)
    if not class_data:
        flash('Class not found', 'error')
        return redirect(url_for('.dashboard'))
    
    # Check if teacher is assigned to this class
    teacher_classes = class_service.get_user_classes(request.user_id, 'teacher')
    if not any(c['id'] == class_id for c in teacher_classes):
        flash('You are not assigned to this class', 'error')
        return redirect(url_for('.dashboard'))
    
    # Get attendance data
    students = class_service.get_class_students(class_id)
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Student Name', 'Roll Number', 'Total Days', 'Present Days', 'Absent Days', 'Attendance Rate'])
    
    for student in students:
        stats = attendance_service.get_attendance_stats(student['id'], class_id)
        writer.writerow([
            student['name'],
            student['roll_number'],
            stats['total_days'],
            stats['present_days'],
            stats['absent_days'],
            f"{stats['attendance_rate']}%"
        ])
    
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'attendance_{class_data["name"]}_{date.today()}.csv'
    )

@bp.route('/request_class', methods=['GET', 'POST'])
@teacher_required
@track_activity('teacher_request_class')
def request_class():
    if request.method == 'POST':
        class_name = request.form['class_name']
        description = request.form['description']
        
        request_id = class_request_service.create_class_request(
            request.user_id, class_name, description
        )
        
        if request_id:
            flash('Class request submitted successfully!', 'success')
            return redirect(url_for('.dashboard'))
        else:
            flash('Failed to submit request', 'error')
    
    return render_template('teacher/request_class.html')

@bp.route('/attendance/start_session', methods=['POST'])
@teacher_required
def start_attendance_session():
    class_id = request.form.get('class_id')
    session_id = attendance_session_service.start_session(class_id, request.user_id)
    flash('Attendance session started.', 'success')
    return redirect(url_for('.live_preview_attendance', session_id=session_id))

@bp.route('/attendance/live_preview/<int:session_id>')
@teacher_required
def live_preview_attendance(session_id):
    temp_attendance = attendance_session_service.get_temporary_attendance(session_id)
    unrecognized_faces = attendance_session_service.get_unrecognized_faces(session_id)
    return render_template('teacher/live_preview.html', 
                        temp_attendance=temp_attendance, 
                        unrecognized_faces=unrecognized_faces, 
                        session_id=session_id)

@bp.route('/attendance/review/<int:session_id>')
@teacher_required
def review_attendance(session_id):
    temp_attendance = attendance_session_service.get_temporary_attendance(session_id)
    return render_template('teacher/review_attendance.html', 
                        temp_attendance=temp_attendance, 
                        session_id=session_id)

@bp.route('/attendance/save/<int:session_id>', methods=['POST'])
@teacher_required
def save_attendance(session_id):
    attendance_session_service.finalize_session(session_id)
    flash('Attendance finalized and saved.', 'success')
    return redirect(url_for('.dashboard'))
def start_attendance():
    class_id = request.form.get('class_id', type=int)
    duration = request.form.get('duration', 30, type=int)
    
    # Verify teacher has access to this class
    if not class_service.is_teacher_of_class(request.user_id, class_id):
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
    success = attendance_session_service.start_session(class_id, request.user_id, duration)
    
    if success:
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Failed to start attendance session'})
