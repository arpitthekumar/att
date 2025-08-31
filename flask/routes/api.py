"""API blueprint for HTTP endpoints."""

from flask import Blueprint, jsonify, request
from backend.auth import login_required, teacher_required
from services_provider import (
    user_service, 
    attendance_service, 
    attendance_session_service,
    face_recognition_service
)
import datetime

bp = Blueprint('api', __name__, url_prefix='/api')

@bp.route('/validate-face-quality', methods=['POST'])
@login_required
def validate_face_quality():
    """Validate face quality in the provided image."""
    try:
        data = request.get_json()
        image_data = data.get('image_data')
        
        if not image_data:
            return jsonify({'success': False, 'message': 'No image data provided'})
        
        is_valid, message = user_service.validate_face_quality(image_data)
        return jsonify({'success': is_valid, 'message': message})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@bp.route('/attendance/save', methods=['POST'])
@teacher_required
def save_attendance():
    """Save attendance data to the database."""
    try:
        data = request.get_json()
        class_id = data.get('class_id')
        attendance_date = data.get('attendance_date', datetime.datetime.now().strftime('%Y-%m-%d'))
        records = data.get('records', [])
        
        if not all([class_id, records]):
            return jsonify({'success': False, 'message': 'Missing required parameters'})
        
        # Save attendance records
        success, message = attendance_service.save_attendance_batch(
            int(class_id), 
            attendance_date, 
            records, 
            request.user_id
        )
        
        return jsonify({'success': success, 'message': message})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@bp.route('/face-data-info')
@login_required
def face_data_info():
    """Get face data information for the current user."""
    try:
        info = user_service.get_face_data_info(request.user_id)
        return jsonify(info)
    except Exception as e:
        return jsonify({'exists': False, 'error': str(e)})

@bp.route('/mark-attendance-manual', methods=['POST'])
@teacher_required
def mark_attendance_manual():
    """Mark attendance manually."""
    try:
        data = request.get_json()
        student_id = data.get('student_id')
        class_id = data.get('class_id')
        status = data.get('status')
        attendance_type = data.get('attendance_type', 'Regular')
        remarks = data.get('remarks', '')
        
        if not all([student_id, class_id, status]):
            return jsonify({'success': False, 'message': 'Missing required parameters'})
        
        success, message = attendance_service.mark_attendance_manual(
            int(student_id), int(class_id), status, request.user_id,
            attendance_type=attendance_type, remarks=remarks
        )
        
        return jsonify({'success': success, 'message': message})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@bp.route('/attendance/mark-temp', methods=['POST'])
@teacher_required
def mark_temp_attendance():
    """Mark temporary attendance during an active session."""
    try:
        session_id = request.form.get('session_id')
        student_id = request.form.get('student_id')
        status = request.form.get('status')
        recognized = request.form.get('recognized', True)
        face_image_path = request.form.get('face_image_path')
        
        attendance_session_service.mark_temporary_attendance(
            session_id, student_id, status, recognized, face_image_path
        )
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/recognize-face', methods=['POST'])
@teacher_required
def recognize_face():
    """Recognize a student face from an image."""
    try:
        if 'image' not in request.files:
            return jsonify({'success': False, 'message': 'No image provided'})
        
        image_file = request.files['image']
        class_id = request.form.get('class_id')
        
        if not class_id:
            return jsonify({'success': False, 'message': 'Class ID is required'})
        
        # Validate face quality first
        quality_result = face_recognition_service.validate_face_quality(image_file)
        
        if not quality_result['success']:
            return jsonify({'success': False, 'message': quality_result['message']})
        
        # Reset file pointer
        image_file.seek(0)
        
        # Get students in the class
        students = user_service.get_students_by_class(int(class_id))
        
        if not students:
            return jsonify({'success': False, 'message': 'No students found in this class'})
        
        # Compare face with student faces
        student_id = face_recognition_service.recognize_student(image_file, students)
        
        if student_id:
            # Get student details
            student = user_service.get_user_by_id(student_id)
            
            if student:
                return jsonify({
                    'success': True,
                    'student_id': student_id,
                    'student_name': student.get('name', 'Unknown'),
                    'roll_number': student.get('roll_number', '')
                })
        
        return jsonify({'success': False, 'message': 'Face not recognized'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})
