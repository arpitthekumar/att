"""API blueprint for HTTP endpoints."""

from flask import Blueprint, jsonify, request
from backend.auth import login_required, teacher_required
from services_provider import (
    user_service, 
    attendance_service, 
    attendance_session_service
)

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
