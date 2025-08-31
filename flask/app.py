from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify, session
from datetime import datetime, date
import csv
import io
import os

# Import backend modules
from backend.database import Database
from backend.auth import Auth, login_required, admin_required, teacher_required, student_required, track_activity
from backend.services import UserService, ClassService, AttendanceService, ClassRequestService, DashboardService, ActivityService, AttendanceSessionService

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Register blueprints
from routes import auth, admin, teacher, student, api
app.register_blueprint(auth.bp)
app.register_blueprint(admin.bp)
app.register_blueprint(teacher.bp)
app.register_blueprint(student.bp)
app.register_blueprint(api.bp)

# Add custom filters
@app.template_filter('datetime')
def format_datetime(value):
    if value is None:
        return ""
    if isinstance(value, (int, float)):
        value = datetime.fromtimestamp(value)
    return value.strftime('%Y-%m-%d %H:%M:%S')

# Add context processor to make session available in all templates
@app.context_processor
def inject_session():
    return {'session': session}

# Initialize services
auth = Auth()
user_service = UserService()
class_service = ClassService()
attendance_service = AttendanceService()
class_request_service = ClassRequestService()
dashboard_service = DashboardService()
activity_service = ActivityService()
attendance_session_service = AttendanceSessionService()

# Initialize database
db = Database()
db.init_db()

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/debug')
def debug():
    """Debug route to check session and navigation"""
    debug_info = {
        'session_keys': list(session.keys()),
        'session_user_id': session.get('user_id'),
        'session_role': session.get('role'),
        'session_name': session.get('name'),
        'session_username': session.get('username'),
        'session_email': session.get('email'),
        'session_login_time': session.get('login_time'),
    }
    return f"<pre>{debug_info}</pre>"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = auth.authenticate(username, password)
        if user:
            auth.login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    auth.logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
@track_activity('dashboard_view')
def dashboard():
    role = session.get('role')
    
    if role == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif role == 'teacher':
        return redirect(url_for('teacher_dashboard'))
    elif role == 'student':
        # Check if student has face data before redirecting
        face_data_info = user_service.get_face_data_info(session['user_id'])
        if not face_data_info.get('exists', False):
            flash('Please set up your face data for attendance', 'warning')
            return redirect(url_for('face_capture'))
        return redirect(url_for('student_dashboard'))
    
    return redirect(url_for('login'))

# Admin Routes
@app.route('/admin/dashboard')
@admin_required
@track_activity('admin_dashboard')
def admin_dashboard():
    data = dashboard_service.get_admin_dashboard_data()
    
    # Get current user information
    user = user_service.get_user_by_id(session['user_id'])
    
    return render_template('admin/dashboard.html', 
                         total_students=data['total_students'],
                         total_teachers=data['total_teachers'],
                         total_classes=data['total_classes'],
                         today_attendance=data['today_attendance'],
                         recent_activity=data['recent_activity'],
                         active_teachers=data['active_teachers'])

@app.route('/admin/users')
@admin_required
@track_activity('admin_users')
def admin_users():
    role_filter = request.args.get('role')
    users = user_service.get_all_users(role_filter)
    return render_template('admin/users.html', users=users)

@app.route('/admin/add_user', methods=['GET', 'POST'])
@admin_required
@track_activity('admin_add_user')
def admin_add_user():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        name = request.form['name']
        role = request.form['role']
        
        user_id = user_service.create_user(username, password, email, name, role)
        
        if user_id:
            # Handle class assignment for students
            if role == 'student':
                class_id = request.form.get('class_id')
                roll_number = request.form.get('roll_number')
                face_data = request.form.get('face_data')
                
                if class_id and roll_number:
                    class_service.assign_student_to_class(user_id, int(class_id), roll_number)
                
                # Handle face data capture for students
                if face_data:
                    try:
                        success, message = user_service.capture_user_face(user_id, 'upload', face_data)
                        if success:
                            flash('User created successfully with face data!', 'success')
                        else:
                            flash(f'User created but face data failed: {message}', 'warning')
                    except Exception as e:
                        flash(f'User created but face data error: {str(e)}', 'warning')
                else:
                    flash('User created successfully! Face data can be added later.', 'success')
            else:
                flash('User created successfully!', 'success')
            
            return redirect(url_for('admin_users'))
        else:
            flash('Failed to create user. Username or email may already exist.', 'error')
    
    classes = class_service.get_all_classes()
    return render_template('admin/add_user.html', classes=classes)

@app.route('/admin/classes', methods=['GET', 'POST'])
@admin_required
@track_activity('admin_classes')
def admin_classes():
    if request.method == 'POST':
        class_name = request.form['class_name']
        teacher_ids = request.form.getlist('teacher_ids[]')
        
        # Create the class
        class_id = class_service.create_class(class_name)
        
        if class_id:
            # Assign teachers if selected
            for teacher_id in teacher_ids:
                class_service.assign_teacher_to_class(int(teacher_id), class_id)
            
            flash('Class created successfully!', 'success')
            return redirect(url_for('admin_classes'))
        else:
            flash('Failed to create class. Class name may already exist.', 'error')
    
    classes = class_service.get_all_classes()
    teachers = user_service.get_all_users('teacher')
    return render_template('admin/classes.html', classes=classes, teachers=teachers)

@app.route('/admin/classes/edit/<int:class_id>', methods=['GET', 'POST'])
@admin_required
@track_activity('admin_edit_class')
def admin_edit_class(class_id):
    class_data = class_service.get_class_by_id(class_id)
    if not class_data:
        flash('Class not found', 'error')
        return redirect(url_for('admin_classes'))
    
    if request.method == 'POST':
        class_name = request.form['class_name']
        teacher_ids = request.form.getlist('teacher_ids[]')
        
        # Update class name
        class_service.update_class(class_id, class_name)
        
        # Remove all current teacher assignments
        current_teachers = class_service.get_class_teachers(class_id)
        for teacher in current_teachers:
            class_service.remove_teacher_from_class(teacher['id'], class_id)
        
        # Add new teacher assignments
        for teacher_id in teacher_ids:
            class_service.assign_teacher_to_class(int(teacher_id), class_id)
        
        flash('Class updated successfully!', 'success')
        return redirect(url_for('admin_classes'))
    
    teachers = user_service.get_all_users('teacher')
    class_teachers = class_service.get_class_teachers(class_id)
    current_teacher_ids = [teacher['id'] for teacher in class_teachers]
    
    return render_template('admin/edit_class.html', 
                         class_data=class_data, 
                         teachers=teachers,
                         current_teacher_ids=current_teacher_ids)

@app.route('/admin/classes/students/<int:class_id>')
@admin_required
@track_activity('admin_class_students')
def admin_class_students(class_id):
    class_data = class_service.get_class_by_id(class_id)
    if not class_data:
        flash('Class not found', 'error')
        return redirect(url_for('admin_classes'))
    
    students = class_service.get_class_students(class_id)
    
    return render_template('admin/class_students.html', 
                         class_data=class_data, 
                         students=students)

@app.route('/admin/classes/reports/<int:class_id>')
@admin_required
@track_activity('admin_class_reports')
def admin_class_reports(class_id):
    class_data = class_service.get_class_by_id(class_id)
    if not class_data:
        flash('Class not found', 'error')
        return redirect(url_for('admin_classes'))
    
    students = class_service.get_class_students(class_id)
    
    # Add attendance statistics for each student
    for student in students:
        stats = attendance_service.get_attendance_stats(student['id'], class_id)
        student.update(stats)
    
    return render_template('admin/class_reports.html', 
                         class_data=class_data, 
                         students=students)

@app.route('/admin/classes/delete/<int:class_id>', methods=['POST'])
@admin_required
@track_activity('admin_delete_class')
def admin_delete_class(class_id):
    success = class_service.delete_class(class_id)
    
    if success:
        flash('Class deleted successfully!', 'success')
    else:
        flash('Failed to delete class.', 'error')
    
    return redirect(url_for('admin_classes'))

@app.route('/admin/requests')
@admin_required
@track_activity('admin_requests')
def admin_requests():
    requests = class_request_service.get_pending_requests()
    return render_template('admin/requests.html', requests=requests)

@app.route('/admin/activity')
@admin_required
@track_activity('admin_activity')
def admin_activity():
    hours = request.args.get('hours', 24, type=int)
    role_filter = request.args.get('role')
    
    if role_filter:
        activities = activity_service.get_recent_activity(hours, role_filter)
    else:
        activities = activity_service.get_recent_activity(hours)
    
    active_users = activity_service.get_active_users(hours)
    
    return render_template('admin/activity.html', 
                         activities=activities, 
                         active_users=active_users,
                         hours=hours,
                         role_filter=role_filter)

@app.route('/admin/teacher_activity')
@admin_required
@track_activity('admin_teacher_activity')
def admin_teacher_activity():
    hours = request.args.get('hours', 24, type=int)
    teacher_activities = activity_service.get_teacher_activity(hours)
    active_teachers = [u for u in activity_service.get_active_users(hours) if u['role'] == 'teacher']
    
    return render_template('admin/teacher_activity.html', 
                         activities=teacher_activities,
                         active_teachers=active_teachers,
                         hours=hours)

@app.route('/admin/approve_request/<int:request_id>')
@admin_required
@track_activity('admin_approve_request')
def admin_approve_request(request_id):
    if class_request_service.approve_request(request_id, session['user_id']):
        flash('Class request approved!', 'success')
    else:
        flash('Failed to approve request', 'error')
    return redirect(url_for('admin_requests'))

@app.route('/admin/reject_request/<int:request_id>')
@admin_required
@track_activity('admin_reject_request')
def admin_reject_request(request_id):
    if class_request_service.reject_request(request_id, session['user_id']):
        flash('Class request rejected!', 'success')
    else:
        flash('Failed to reject request', 'error')
    return redirect(url_for('admin_requests'))

# Teacher Routes
@app.route('/teacher/dashboard')
@teacher_required
@track_activity('teacher_dashboard')
def teacher_dashboard():
    data = dashboard_service.get_teacher_dashboard_data(session['user_id'])
    
    # Get current user information
    user = user_service.get_user_by_id(session['user_id'])
    
    return render_template('teacher/dashboard.html', 
                         classes=data['classes'],
                         today_attendance=data['today_attendance'],
                         session={'name': user['name']})

@app.route('/teacher/attendance/<int:class_id>')
@teacher_required
@track_activity('teacher_attendance')
def teacher_attendance(class_id):
    class_data = class_service.get_class_by_id(class_id)
    if not class_data:
        flash('Class not found', 'error')
        return redirect(url_for('teacher_dashboard'))
    
    # Check if teacher is assigned to this class
    teacher_classes = class_service.get_user_classes(session['user_id'], 'teacher')
    if not any(c['id'] == class_id for c in teacher_classes):
        flash('You are not assigned to this class', 'error')
        return redirect(url_for('teacher_dashboard'))
    
    today = date.today()
    attendance = attendance_service.get_class_attendance(class_id, today)
    students = class_service.get_class_students(class_id)
    
    # Get or create attendance session for today
    session_id = None
    sessions = db.get_db().cursor().execute('SELECT id FROM attendance_sessions WHERE class_id = ? AND teacher_id = ? AND date = ? AND status = "In Progress"', (class_id, session['user_id'], today)).fetchone()
    if sessions:
        session_id = sessions['id']
    else:
        session_id = attendance_session_service.start_session(class_id, session['user_id'])

    temp_attendance = attendance_session_service.get_temporary_attendance(session_id)
    unrecognized_faces = attendance_session_service.get_unrecognized_faces(session_id)

    return render_template('teacher/attendance.html', 
                         class_data=class_data, 
                         students=students, 
                         attendance=attendance,
                         today=today,
                         temp_attendance=temp_attendance,
                         unrecognized_faces=unrecognized_faces,
                         session_id=session_id)

@app.route('/teacher/attendance/start', methods=['POST'])
@teacher_required
@track_activity('teacher_start_attendance')
def teacher_start_attendance():
    class_id = request.form.get('class_id')
    student_id = request.form.get('student_id')
    attendance_type = request.form.get('attendance_type', 'regular')
    remarks = request.form.get('remarks', '')
    
    if not class_id or not student_id:
        return jsonify({'success': False, 'message': 'Missing parameters'})
    
    # Verify teacher is assigned to this class
    teacher_classes = class_service.get_user_classes(session['user_id'], 'teacher')
    if not any(c['id'] == int(class_id) for c in teacher_classes):
        return jsonify({'success': False, 'message': 'Not authorized for this class'})
    
    # Check if student is in this class
    students = class_service.get_class_students(int(class_id))
    if not any(s['id'] == int(student_id) for s in students):
        return jsonify({'success': False, 'message': 'Student not in this class'})
    
    # Mark attendance with face recognition
    success, message = attendance_service.mark_attendance_with_face(
        int(student_id), int(class_id), session['user_id'], attendance_type, remarks
    )
    
    return jsonify({'success': success, 'message': message})

@app.route('/teacher/reports/<int:class_id>')
@teacher_required
@track_activity('teacher_reports')
def teacher_reports(class_id):
    class_data = class_service.get_class_by_id(class_id)
    if not class_data:
        flash('Class not found', 'error')
        return redirect(url_for('teacher_dashboard'))
    
    # Check if teacher is assigned to this class
    teacher_classes = class_service.get_user_classes(session['user_id'], 'teacher')
    if not any(c['id'] == class_id for c in teacher_classes):
        flash('You are not assigned to this class', 'error')
        return redirect(url_for('teacher_dashboard'))
    
    students = class_service.get_class_students(class_id)
    
    # Add attendance statistics for each student
    for student in students:
        stats = attendance_service.get_attendance_stats(student['id'], class_id)
        student.update(stats)
    
    return render_template('teacher/reports.html', class_data=class_data, students=students)

@app.route('/api/attendance/class/<int:class_id>/range')
@teacher_required
def get_class_attendance_by_date_range(class_id):
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not start_date or not end_date:
        return jsonify({'success': False, 'message': 'Start date and end date are required'})
    
    try:
        # Validate dates
        datetime.strptime(start_date, '%Y-%m-%d')
        datetime.strptime(end_date, '%Y-%m-%d')
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid date format. Use YYYY-MM-DD'})
    
    # Check if teacher is assigned to this class
    teacher_classes = class_service.get_user_classes(session['user_id'], 'teacher')
    if not any(c['id'] == class_id for c in teacher_classes):
        return jsonify({'success': False, 'message': 'You are not assigned to this class'})
    
    # Get attendance data for the date range
    attendance_data = attendance_service.get_class_attendance_by_date_range(class_id, start_date, end_date)
    
    return jsonify({
        'success': True, 
        'attendance': attendance_data
    })

@app.route('/teacher/export/<int:class_id>')
@teacher_required
@track_activity('teacher_export')
def teacher_export(class_id):
    class_data = class_service.get_class_by_id(class_id)
    if not class_data:
        flash('Class not found', 'error')
        return redirect(url_for('teacher_dashboard'))
    
    # Check if teacher is assigned to this class
    teacher_classes = class_service.get_user_classes(session['user_id'], 'teacher')
    if not any(c['id'] == class_id for c in teacher_classes):
        flash('You are not assigned to this class', 'error')
        return redirect(url_for('teacher_dashboard'))
    
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

@app.route('/teacher/request_class', methods=['GET', 'POST'])
@teacher_required
@track_activity('teacher_request_class')
def teacher_request_class():
    if request.method == 'POST':
        class_name = request.form['class_name']
        description = request.form['description']
        
        request_id = class_request_service.create_class_request(
            session['user_id'], class_name, description
        )
        
        if request_id:
            flash('Class request submitted successfully!', 'success')
            return redirect(url_for('teacher_dashboard'))
        else:
            flash('Failed to submit request', 'error')
    
    return render_template('teacher/request_class.html')

# Student Routes
@app.route('/student/dashboard')
@student_required
@track_activity('student_dashboard')
def student_dashboard():
    data = dashboard_service.get_student_dashboard_data(session['user_id'])
    
    # Get current user information
    user = user_service.get_user_by_id(session['user_id'])
    
    # Get student's class information
    student_classes = class_service.get_user_classes(session['user_id'], 'student')
    class_info = student_classes[0] if student_classes else None
    
    # Get face data information including the image
    face_data = user_service.get_face_data_info(session['user_id'])
    
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

@app.route('/student/attendance')
@student_required
@track_activity('student_attendance')
def student_attendance():
    # Get current user information
    user = user_service.get_user_by_id(session['user_id'])
    
    # Get student's class information
    student_classes = class_service.get_user_classes(session['user_id'], 'student')
    class_info = student_classes[0] if student_classes else None
    
    # Create student object with required fields
    student = {
        'id': user['id'],
        'student_name': user['name'],
        'roll_number': class_info['roll_number'] if class_info else None,
        'class_name': class_info['name'] if class_info else 'Not assigned'
    }
    
    # Get attendance records
    attendance_records = attendance_service.get_student_attendance(session['user_id'])
    
    return render_template('student/attendance.html', 
                         student=student,
                         records=attendance_records)

@app.route('/face_capture')
@login_required
@track_activity('face_capture')
def face_capture():
    """Face capture page for all users"""
    return render_template('face_capture.html')

@app.route('/api/validate-face-quality', methods=['POST'])
@login_required
def validate_face_quality():
    """API endpoint to validate face quality"""
    try:
        data = request.get_json()
        image_data = data.get('image_data')
        pose = data.get('pose')
        
        if not image_data:
            return jsonify({'success': False, 'message': 'No image data provided'})
        
        is_valid, message = user_service.validate_face_quality(image_data, pose)
        return jsonify({'success': is_valid, 'message': message})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/api/capture-face', methods=['POST'])
@login_required
def capture_face():
    """API endpoint to capture face data or multi-pose embedding"""
    try:
        data = request.get_json()
        method = data.get('method', 'camera')
        image_data = data.get('image_data')
        pose = data.get('pose', 'front')
        
        if method == 'upload' and image_data:
            success, result = user_service.capture_user_face(session['user_id'], 'upload', image_data, pose)
        else:
            success, result = user_service.capture_user_face(session['user_id'], 'camera')
        
        return jsonify({'success': success, 'message': result})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/api/face-data-info')
@login_required
def face_data_info():
    """API endpoint to get face data information"""
    try:
        info = user_service.get_face_data_info(session['user_id'])
        return jsonify(info)
    except Exception as e:
        return jsonify({'exists': False, 'error': str(e)})

@app.route('/api/backfill-face-embeddings', methods=['POST'])
@admin_required
def backfill_face_embeddings():
    try:
        data = request.get_json() or {}
        user_id = data.get('user_id') or session.get('user_id')
        poses = data.get('poses', ['front'])
        success, message = user_service.backfill_embeddings_from_image(int(user_id), poses)
        return jsonify({'success': success, 'message': message})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/api/delete-face-data', methods=['DELETE'])
@login_required
def delete_face_data():
    """API endpoint to delete face data"""
    try:
        success = user_service.face_recognition.delete_face_data(session['user_id'])
        return jsonify({'success': success, 'message': 'Face data deleted successfully' if success else 'No face data to delete'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/api/mark-attendance-manual', methods=['POST'])
@teacher_required
def mark_attendance_manual():
    """API endpoint to mark attendance manually"""
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
            int(student_id), int(class_id), status, session['user_id'],
            attendance_type=attendance_type, remarks=remarks
        )
        
        return jsonify({'success': success, 'message': message})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/student/capture_face')
@student_required
@track_activity('student_capture_face')
def student_capture_face():
    success, message = user_service.capture_user_face(session['user_id'])
    if success:
        flash('Face data captured successfully!', 'success')
    else:
        flash(f'Failed to capture face: {message}', 'error')
    return redirect(url_for('student_dashboard'))

@app.route('/faces/<filename>')
@login_required
def serve_face(filename):
    """Serve face images"""
    return send_file(os.path.join('faces', filename))

@app.route('/api/face-image')
@login_required
def get_face_image():
    """Get the current user's face image for download"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Not logged in'}), 401
    
    face_file = os.path.join('faces', f'user_{user_id}.jpg')
    if not os.path.exists(face_file):
        return jsonify({'error': 'No face image found'}), 404
    
    return send_file(face_file, as_attachment=True, download_name=f'face_image_{user_id}.jpg')

@app.route('/teacher/attendance/start_session', methods=['POST'])
@teacher_required
def start_attendance_session():
    class_id = request.form.get('class_id')
    teacher_id = session.get('user_id')
    session_id = attendance_session_service.start_session(class_id, teacher_id)
    flash('Attendance session started.', 'success')
    return redirect(url_for('live_preview_attendance', session_id=session_id))

@app.route('/teacher/attendance/live_preview/<int:session_id>')
@teacher_required
def live_preview_attendance(session_id):
    temp_attendance = attendance_session_service.get_temporary_attendance(session_id)
    unrecognized_faces = attendance_session_service.get_unrecognized_faces(session_id)
    return render_template('teacher/live_preview.html', temp_attendance=temp_attendance, unrecognized_faces=unrecognized_faces, session_id=session_id)

@app.route('/teacher/attendance/mark_temp', methods=['POST'])
@teacher_required
def mark_temp_attendance():
    session_id = request.form.get('session_id')
    student_id = request.form.get('student_id')
    status = request.form.get('status')
    recognized = request.form.get('recognized', True)
    face_image_path = request.form.get('face_image_path')
    attendance_session_service.mark_temporary_attendance(session_id, student_id, status, recognized, face_image_path)
    return jsonify({'success': True})

@app.route('/teacher/attendance/add_unrecognized', methods=['POST'])
@teacher_required
def add_unrecognized_face():
    session_id = request.form.get('session_id')
    face_image_path = request.form.get('face_image_path')
    attendance_session_service.add_unrecognized_face(session_id, face_image_path)
    return jsonify({'success': True})

@app.route('/teacher/attendance/assign_face', methods=['POST'])
@teacher_required
def assign_unrecognized_face():
    session_id = request.form.get('session_id')
    student_id = request.form.get('student_id')
    face_image_path = request.form.get('face_image_path')
    attendance_session_service.assign_unrecognized_face(session_id, student_id, face_image_path)
    return jsonify({'success': True})

@app.route('/teacher/attendance/review/<int:session_id>')
@teacher_required
def review_attendance(session_id):
    temp_attendance = attendance_session_service.get_temporary_attendance(session_id)
    return render_template('teacher/review_attendance.html', temp_attendance=temp_attendance, session_id=session_id)

@app.route('/teacher/attendance/save/<int:session_id>', methods=['POST'])
@teacher_required
def save_attendance(session_id):
    # Here, move temp attendance to final attendance table and finalize session
    # You can add logic to save each record to Attendance table
    attendance_session_service.finalize_session(session_id)
    flash('Attendance finalized and saved.', 'success')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
