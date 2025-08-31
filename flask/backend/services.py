from datetime import datetime, date
from .database import Database
from .models import User, Class, ClassAssignment, Attendance, ClassRequest, UserActivity, AttendanceSession, TemporaryAttendance, UnrecognizedFace
from .face_recognition import FaceRecognition
import cv2
import numpy as np
from PIL import Image
import io
import base64

class AttendanceSessionService:
    def __init__(self):
        self.db = Database()
        self.session_model = AttendanceSession(self.db)
        self.temp_attendance_model = TemporaryAttendance(self.db)
        self.unrec_face_model = UnrecognizedFace(self.db)

    def start_session(self, class_id, teacher_id):
        return self.session_model.create(class_id, teacher_id)

    def finalize_session(self, session_id):
        self.session_model.finalize(session_id)
        self.temp_attendance_model.delete_by_session(session_id)
        self.unrec_face_model.delete_by_session(session_id)

    def mark_temporary_attendance(self, session_id, student_id, status, recognized=True, face_image_path=None):
        self.temp_attendance_model.mark(session_id, student_id, status, recognized, face_image_path)

    def get_temporary_attendance(self, session_id):
        return self.temp_attendance_model.get_by_session(session_id)

    def add_unrecognized_face(self, session_id, face_image_path):
        self.unrec_face_model.add(session_id, face_image_path)

    def get_unrecognized_faces(self, session_id):
        return self.unrec_face_model.get_by_session(session_id)

    def assign_unrecognized_face(self, session_id, student_id, face_image_path):
        self.temp_attendance_model.mark(session_id, student_id, 'Present (Temporary)', True, face_image_path)

class UserService:
    def __init__(self):
        self.db = Database()
        self.user_model = User(self.db)
        self.face_recognition = FaceRecognition()
        self.activity_model = UserActivity(self.db)
    
    def create_user(self, username, password, email, name, role):
        """Create a new user"""
        return self.user_model.create(username, password, email, name, role)
    
    def get_user_by_username(self, username):
        """Get user by username"""
        return self.user_model.get_by_username(username)
    
    def get_user_by_id(self, user_id):
        """Get user by ID"""
        return self.user_model.get_by_id(user_id)
    
    def get_all_users(self, role=None):
        """Get all users, optionally filtered by role"""
        return self.user_model.get_all(role)
    
    def capture_user_face(self, user_id, method='camera', image_data=None, pose='front'):
        """Capture face data/embedding for a user with quality validation"""
        return self.face_recognition.capture_face(user_id, method, image_data, pose)
    
    def validate_face_quality(self, image_data, pose=None):
        """Validate face quality from image data, with optional pose guidance"""
        try:
            # Decode base64 image data
            if image_data.startswith('data:image'):
                image_data = image_data.split(',')[1]
            
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            return self.face_recognition.validate_face_quality(opencv_image, pose)
        except Exception as e:
            return False, f"Error validating image: {str(e)}"
    
    def get_face_data_info(self, user_id):
        """Get information about user's face data"""
        return self.face_recognition.get_face_data_info(user_id)
    
    def has_face_data(self, user_id):
        """Check if user has face data"""
        return self.face_recognition.has_face_data(user_id)

    def backfill_embeddings_from_image(self, user_id, poses=("front",)):
        """If a legacy face image exists, compute embeddings for given poses using same image."""
        from PIL import Image
        import os
        import numpy as np
        import cv2
        face_path = os.path.join(self.face_recognition.faces_dir, f'user_{user_id}.jpg')
        if not os.path.exists(face_path):
            return False, "No legacy face image found"
        image = Image.open(face_path)
        opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        vector = self.face_recognition.compute_embedding_from_image(opencv_image)
        if vector is None:
            return False, "Failed to compute embedding from image"
        for p in poses:
            self.face_recognition.store_embedding(user_id, p, vector)
        return True, f"Backfilled embeddings for poses: {', '.join(poses)}"
    
    def get_user_activity(self, user_id, limit=50):
        """Get activity for a specific user"""
        return self.activity_model.get_user_activity(user_id, limit)

class ClassService:
    def __init__(self):
        self.db = Database()
        self.class_model = Class(self.db)
        self.assignment_model = ClassAssignment(self.db)
    
    def create_class(self, name, description=""):
        """Create a new class"""
        return self.class_model.create(name, description)
        
    def delete_class(self, class_id):
        """Delete a class and all its assignments"""
        return self.class_model.delete(class_id)
    
    def get_all_classes(self):
        """Get all classes with teacher names and student counts"""
        classes = self.class_model.get_all()
        
        # Convert sqlite3.Row objects to dictionaries and enhance with additional data
        enhanced_classes = []
        for class_data in classes:
            # Convert to dict
            class_dict = dict(class_data)
            
            # Get all teachers for this class
            teachers = self.get_class_teachers(class_dict['id'])
            if teachers:
                # Store all teacher names in a list
                class_dict['teachers'] = [teacher['name'] for teacher in teachers]
                # Keep teacher_name for backward compatibility
                class_dict['teacher_name'] = teachers[0]['name'] if teachers else None
            else:
                class_dict['teachers'] = []
                class_dict['teacher_name'] = None
            
            # Get student count
            students = self.get_class_students(class_dict['id'])
            class_dict['student_count'] = len(students)
            
            enhanced_classes.append(class_dict)
        
        return enhanced_classes
    
    def get_class_by_id(self, class_id):
        """Get class by ID"""
        return self.class_model.get_by_id(class_id)
    
    def get_class_teachers(self, class_id):
        """Get all teachers assigned to a class"""
        return self.class_model.get_teachers(class_id)
    
    def get_class_students(self, class_id):
        """Get all students in a class"""
        students = self.class_model.get_students(class_id)
        
        # Convert sqlite3.Row objects to dictionaries
        formatted_students = []
        for student in students:
            student_dict = dict(student)
            formatted_students.append(student_dict)
        
        return formatted_students
    
    def update_class(self, class_id, name, description=None):
        """Update a class name and description"""
        return self.class_model.update(class_id, name, description)
    
    def assign_teacher_to_class(self, user_id, class_id):
        """Assign a teacher to a class"""
        return self.assignment_model.assign_teacher(user_id, class_id)
        
    def remove_teacher_from_class(self, user_id, class_id):
        """Remove a teacher from a class"""
        return self.assignment_model.remove_teacher(user_id, class_id)
    
    def assign_student_to_class(self, user_id, class_id, roll_number):
        """Assign a student to a class with roll number"""
        return self.assignment_model.assign_student(user_id, class_id, roll_number)
    
    def get_user_classes(self, user_id, role):
        """Get all classes for a user based on their role"""
        classes = self.assignment_model.get_user_classes(user_id, role)
        
        # Convert sqlite3.Row objects to dictionaries
        formatted_classes = []
        for class_item in classes:
            class_dict = dict(class_item)
            formatted_classes.append(class_dict)
        
        return formatted_classes

class AttendanceService:
    def __init__(self):
        self.db = Database()
        self.attendance_model = Attendance(self.db)
        self.face_recognition = FaceRecognition()
    
    def mark_attendance(self, user_id, class_id, date, status, marked_by, remarks=None, attendance_type="regular"):
        """Mark attendance for a student with optional remarks and attendance type"""
        return self.attendance_model.mark_attendance(user_id, class_id, date, status, marked_by, remarks, attendance_type)
    
    def get_class_attendance(self, class_id, date):
        """Get attendance for a class on a specific date"""
        attendance_records = self.attendance_model.get_class_attendance(class_id, date)
        
        # Convert sqlite3.Row objects to dictionaries
        formatted_records = []
        for record in attendance_records:
            record_dict = dict(record)
            
            # Format date and time if marked_at exists
            if 'marked_at' in record_dict and record_dict['marked_at']:
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(record_dict['marked_at'].replace('Z', '+00:00'))
                    record_dict['date'] = dt.strftime('%Y-%m-%d')
                    record_dict['time'] = dt.strftime('%H:%M')
                except:
                    record_dict['date'] = str(record_dict.get('date', ''))
                    record_dict['time'] = 'N/A'
            else:
                record_dict['date'] = str(record_dict.get('date', ''))
                record_dict['time'] = 'N/A'
            
            formatted_records.append(record_dict)
        
        return formatted_records
    
    def get_student_attendance(self, user_id, class_id=None, start_date=None, end_date=None):
        """Get attendance records for a student with formatted data"""
        records = self.attendance_model.get_student_attendance(user_id, class_id, start_date, end_date)
        
        # Convert sqlite3.Row objects to dictionaries and format data
        formatted_records = []
        for record in records:
            record_dict = dict(record)
            
            # Format date and time if marked_at exists
            if 'marked_at' in record_dict and record_dict['marked_at']:
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(record_dict['marked_at'].replace('Z', '+00:00'))
                    record_dict['date'] = dt.strftime('%Y-%m-%d')
                    record_dict['time'] = dt.strftime('%H:%M')
                except:
                    record_dict['date'] = str(record_dict.get('date', ''))
                    record_dict['time'] = 'N/A'
            else:
                record_dict['date'] = str(record_dict.get('date', ''))
                record_dict['time'] = 'N/A'
            
            formatted_records.append(record_dict)
        
        return formatted_records
        
    def get_class_attendance_by_date_range(self, class_id, start_date, end_date):
        """Get attendance for a class within a specific date range"""
        attendance_records = self.attendance_model.get_class_attendance_by_date_range(class_id, start_date, end_date)
        
        # Convert sqlite3.Row objects to dictionaries
        formatted_records = []
        for record in attendance_records:
            record_dict = dict(record)
            
            # Format date and time if marked_at exists
            if 'marked_at' in record_dict and record_dict['marked_at']:
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(record_dict['marked_at'].replace('Z', '+00:00'))
                    record_dict['date'] = dt.strftime('%Y-%m-%d')
                    record_dict['time'] = dt.strftime('%H:%M')
                except:
                    record_dict['date'] = str(record_dict.get('date', ''))
                    record_dict['time'] = 'N/A'
            else:
                record_dict['date'] = str(record_dict.get('date', ''))
                record_dict['time'] = 'N/A'
            
            formatted_records.append(record_dict)
        
        return formatted_records
    
    def mark_attendance_with_face(self, user_id, class_id, marked_by, attendance_type="regular", remarks=None):
        """Mark attendance using face recognition with strict validation"""
        # First verify the user has face data
        if not self.face_recognition.has_face_data(user_id):
            return False, "No face data found for this user. Please capture face data first."
            
    def save_attendance_batch(self, class_id, attendance_date, records, marked_by):
        """Save batch attendance records for a class"""
        try:
            # Validate inputs
            if not class_id or not records:
                return False, "Missing required parameters"
                
            # Format date if needed
            if isinstance(attendance_date, str):
                attendance_date = attendance_date.split('T')[0]  # Handle ISO format
                
            # Process each record
            success_count = 0
            for record in records:
                student_id = record.get('student_id')
                status = record.get('status')
                timestamp = record.get('timestamp')
                attendance_type = record.get('type', 'Regular')
                remarks = record.get('remarks', '')
                
                if student_id and status:
                    # Mark attendance for this student
                    self.attendance_model.mark_attendance(
                        student_id, 
                        class_id, 
                        attendance_date, 
                        status, 
                        marked_by, 
                        remarks, 
                        attendance_type
                    )
                    success_count += 1
            
            return True, f"Successfully saved {success_count} attendance records"
            
        except Exception as e:
            return False, f"Error saving attendance: {str(e)}"
        
        # Check if attendance already marked for today
        today = date.today()
        existing_attendance = self.get_student_attendance(user_id, class_id)
        for record in existing_attendance:
            if record['date'] == today:
                return False, "Attendance already marked for today"
        
        # Perform face recognition with strict validation
        success, message = self.face_recognition.recognize_face(user_id, max_attempts=3)
        
        if success:
            # Mark attendance if face recognition succeeds
            attendance_id = self.mark_attendance(user_id, class_id, today, 'present', marked_by, remarks, attendance_type)
            if attendance_id:
                return True, "Attendance marked successfully with face recognition"
            else:
                return False, "Failed to mark attendance in database"
        else:
            return False, f"Face recognition failed: {message}. Please try again."
    
    def mark_attendance_manual(self, user_id, class_id, status, marked_by, attendance_type="regular", remarks=None):
        """Mark attendance manually (for teachers/admins)"""
        today = date.today()
        
        # Check if attendance already marked for today
        existing_attendance = self.get_student_attendance(user_id, class_id)
        for record in existing_attendance:
            if record['date'] == today:
                return False, "Attendance already marked for today"
        
        attendance_id = self.mark_attendance(user_id, class_id, today, status, marked_by, remarks, attendance_type)
        if attendance_id:
            return True, f"Attendance marked as {status}"
        else:
            return False, "Failed to mark attendance"
    
    def get_attendance_stats(self, user_id, class_id=None):
        """Get attendance statistics for a student"""
        attendance_records = self.get_student_attendance(user_id, class_id)
        
        total_days = len(attendance_records)
        present_days = len([r for r in attendance_records if r['status'] == 'present'])
        
        if total_days > 0:
            attendance_rate = (present_days / total_days) * 100
        else:
            attendance_rate = 0
        
        return {
            'total_days': total_days,
            'present_days': present_days,
            'absent_days': total_days - present_days,
            'attendance_rate': round(attendance_rate, 2)
        }

class ClassRequestService:
    def __init__(self):
        self.db = Database()
        self.request_model = ClassRequest(self.db)
    
    def create_class_request(self, teacher_id, class_name, description):
        """Create a new class request"""
        return self.request_model.create_request(teacher_id, class_name, description)
    
    def get_pending_requests(self):
        """Get all pending class requests"""
        return self.request_model.get_pending_requests()
    
    def approve_request(self, request_id, reviewed_by):
        """Approve a class request"""
        return self.request_model.approve_request(request_id, reviewed_by)
    
    def reject_request(self, request_id, reviewed_by):
        """Reject a class request"""
        return self.request_model.reject_request(request_id, reviewed_by)

class ActivityService:
    def __init__(self):
        self.db = Database()
        self.activity_model = UserActivity(self.db)
    
    def log_activity(self, user_id, activity_type, page_url=None, action_description=None, ip_address=None, user_agent=None):
        """Log user activity"""
        return self.activity_model.log_activity(
            user_id=user_id,
            activity_type=activity_type,
            page_url=page_url,
            action_description=action_description,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    def get_recent_activity(self, hours=24, role=None):
        """Get recent activity across all users or filtered by role"""
        return self.activity_model.get_recent_activity(hours, role)
    
    def get_active_users(self, hours=24):
        """Get list of active users in the last N hours"""
        return self.activity_model.get_active_users(hours)
    
    def get_teacher_activity(self, hours=24):
        """Get teacher activity specifically"""
        return self.activity_model.get_recent_activity(hours, 'teacher')
    
    def get_student_activity(self, hours=24):
        """Get student activity specifically"""
        return self.activity_model.get_recent_activity(hours, 'student')

class DashboardService:
    def __init__(self):
        self.db = Database()
        self.user_model = User(self.db)
        self.class_model = Class(self.db)
        self.attendance_model = Attendance(self.db)
        self.activity_model = UserActivity(self.db)
    
    def get_admin_dashboard_data(self):
        """Get data for admin dashboard"""
        users = self.user_model.get_all()
        classes = self.class_model.get_all()
        
        # Count by role
        students = [u for u in users if u['role'] == 'student']
        teachers = [u for u in users if u['role'] == 'teacher']
        
        # Get today's attendance
        today = date.today()
        conn = self.db.get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) as today_attendance 
            FROM attendance 
            WHERE date = ? AND status = 'present'
        ''', (today,))
        today_attendance = cursor.fetchone()['today_attendance']
        conn.close()
        
        # Get recent activity
        recent_activity = self.activity_model.get_recent_activity(hours=24, role='teacher')
        active_teachers = self.activity_model.get_active_users(hours=24)
        
        return {
            'total_students': len(students),
            'total_teachers': len(teachers),
            'total_classes': len(classes),
            'today_attendance': today_attendance,
            'recent_activity': recent_activity[:10],  # Last 10 activities
            'active_teachers': [u for u in active_teachers if u['role'] == 'teacher']
        }
    
    def get_teacher_dashboard_data(self, teacher_id):
        """Get data for teacher dashboard"""
        # Get teacher's classes
        conn = self.db.get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.*, COUNT(ca2.user_id) as student_count
            FROM classes c 
            JOIN class_assignments ca1 ON c.id = ca1.class_id 
            LEFT JOIN class_assignments ca2 ON c.id = ca2.class_id AND ca2.role = 'student'
            WHERE ca1.user_id = ? AND ca1.role = 'teacher'
            GROUP BY c.id
        ''', (teacher_id,))
        classes = cursor.fetchall()
        
        # Get today's attendance for teacher's classes
        today = date.today()
        cursor.execute('''
            SELECT COUNT(*) as today_attendance
            FROM attendance a
            JOIN class_assignments ca ON a.user_id = ca.user_id AND a.class_id = ca.class_id
            WHERE ca.user_id IN (
                SELECT ca2.user_id FROM class_assignments ca2 
                WHERE ca2.class_id IN (
                    SELECT ca3.class_id FROM class_assignments ca3 
                    WHERE ca3.user_id = ? AND ca3.role = 'teacher'
                ) AND ca2.role = 'student'
            ) AND a.date = ? AND a.status = 'present'
        ''', (teacher_id, today))
        today_attendance = cursor.fetchone()['today_attendance']
        conn.close()
        
        return {
            'classes': classes,
            'today_attendance': today_attendance
        }
    
    def get_student_dashboard_data(self, student_id):
        """Get data for student dashboard"""
        # Get student's classes
        conn = self.db.get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.* FROM classes c 
            JOIN class_assignments ca ON c.id = ca.class_id 
            WHERE ca.user_id = ? AND ca.role = 'student'
        ''', (student_id,))
        classes = cursor.fetchall()
        conn.close()
        
        # Get attendance statistics
        attendance_service = AttendanceService()
        stats = attendance_service.get_attendance_stats(student_id)
        
        # Get recent attendance
        recent_attendance = self.attendance_model.get_student_attendance(student_id)[:5]
        
        return {
            'classes': classes,
            'attendance_stats': stats,
            'recent_attendance': recent_attendance
        }
