from werkzeug.security import generate_password_hash, check_password_hash
from .database import Database

class User:
    def __init__(self, db):
        self.db = db
    
    def get_by_username(self, username):
        conn = self.db.get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        return user
    
    def get_by_id(self, user_id):
        conn = self.db.get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        return user
    
    def create(self, username, password, email, name, role):
        conn = self.db.get_db()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO users (username, password_hash, email, name, role) 
                VALUES (?, ?, ?, ?, ?)
            ''', (username, generate_password_hash(password), email, name, role))
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            return user_id
        except:
            conn.close()
            return None
    
    def get_all(self, role=None):
        conn = self.db.get_db()
        cursor = conn.cursor()
        if role:
            cursor.execute('SELECT * FROM users WHERE role = ? ORDER BY name', (role,))
        else:
            cursor.execute('SELECT * FROM users ORDER BY name')
        users = cursor.fetchall()
        conn.close()
        return users

class UserActivity:
    def __init__(self, db):
        self.db = db
    
    def log_activity(self, user_id, activity_type, page_url=None, action_description=None, ip_address=None, user_agent=None):
        conn = self.db.get_db()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO user_activity (user_id, activity_type, page_url, action_description, ip_address, user_agent) 
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, activity_type, page_url, action_description, ip_address, user_agent))
            conn.commit()
            conn.close()
            return True
        except:
            conn.close()
            return False
    
    def get_user_activity(self, user_id, limit=50):
        conn = self.db.get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM user_activity 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (user_id, limit))
        activities = cursor.fetchall()
        conn.close()
        return activities
    
    def get_recent_activity(self, hours=24, role=None):
        conn = self.db.get_db()
        cursor = conn.cursor()
        
        if role:
            cursor.execute('''
                SELECT ua.*, u.name as user_name, u.role 
                FROM user_activity ua 
                JOIN users u ON ua.user_id = u.id 
                WHERE ua.created_at >= datetime('now', '-' || ? || ' hours') AND u.role = ?
                ORDER BY ua.created_at DESC
            ''', (hours, role))
        else:
            cursor.execute('''
                SELECT ua.*, u.name as user_name, u.role 
                FROM user_activity ua 
                JOIN users u ON ua.user_id = u.id 
                WHERE ua.created_at >= datetime('now', '-' || ? || ' hours')
                ORDER BY ua.created_at DESC
            ''', (hours,))
        
        activities = cursor.fetchall()
        conn.close()
        return activities
    
    def get_active_users(self, hours=24):
        conn = self.db.get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT DISTINCT u.id, u.name, u.role, u.username,
                   MAX(ua.created_at) as last_activity,
                   COUNT(ua.id) as activity_count
            FROM users u 
            JOIN user_activity ua ON u.id = ua.user_id 
            WHERE ua.created_at >= datetime('now', '-' || ? || ' hours')
            GROUP BY u.id 
            ORDER BY last_activity DESC
        ''', (hours,))
        active_users = cursor.fetchall()
        conn.close()
        return active_users

class Class:
    def __init__(self, db):
        self.db = db
    
    def create(self, name, description=""):
        conn = self.db.get_db()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO classes (name, description) VALUES (?, ?)', (name, description))
        conn.commit()
        class_id = cursor.lastrowid
        conn.close()
        return class_id
    
    def get_all(self):
        conn = self.db.get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM classes ORDER BY name')
        classes = cursor.fetchall()
        conn.close()
        return classes
    
    def get_by_id(self, class_id):
        conn = self.db.get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM classes WHERE id = ?', (class_id,))
        class_data = cursor.fetchone()
        conn.close()
        return class_data
    
    def get_teachers(self, class_id):
        conn = self.db.get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT u.* FROM users u 
            JOIN class_assignments ca ON u.id = ca.user_id 
            WHERE ca.class_id = ? AND ca.role = 'teacher'
        ''', (class_id,))
        teachers = cursor.fetchall()
        conn.close()
        return teachers
    
    def get_students(self, class_id):
        conn = self.db.get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT u.*, ca.roll_number FROM users u 
            JOIN class_assignments ca ON u.id = ca.user_id 
            WHERE ca.class_id = ? AND ca.role = 'student'
            ORDER BY ca.roll_number
        ''', (class_id,))
        students = cursor.fetchall()
        conn.close()
        return students

class ClassAssignment:
    def __init__(self, db):
        self.db = db
    
    def assign_teacher(self, user_id, class_id):
        conn = self.db.get_db()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO class_assignments (user_id, class_id, role) 
                VALUES (?, ?, 'teacher')
            ''', (user_id, class_id))
            conn.commit()
            conn.close()
            return True
        except:
            conn.close()
            return False
    
    def assign_student(self, user_id, class_id, roll_number):
        conn = self.db.get_db()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO class_assignments (user_id, class_id, role, roll_number) 
                VALUES (?, ?, 'student', ?)
            ''', (user_id, class_id, roll_number))
            conn.commit()
            conn.close()
            return True
        except:
            conn.close()
            return False
    
    def get_user_classes(self, user_id, role):
        conn = self.db.get_db()
        cursor = conn.cursor()
        if role == 'student':
            cursor.execute('''
                SELECT c.*, ca.roll_number FROM classes c 
                JOIN class_assignments ca ON c.id = ca.class_id 
                WHERE ca.user_id = ? AND ca.role = ?
                ORDER BY c.name
            ''', (user_id, role))
        else:
            cursor.execute('''
                SELECT c.* FROM classes c 
                JOIN class_assignments ca ON c.id = ca.class_id 
                WHERE ca.user_id = ? AND ca.role = ?
                ORDER BY c.name
            ''', (user_id, role))
        classes = cursor.fetchall()
        conn.close()
        return classes

class Attendance:
    def __init__(self, db):
        self.db = db
    
    def mark_attendance(self, user_id, class_id, date, status, marked_by):
        conn = self.db.get_db()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO attendance (user_id, class_id, date, status, marked_by) 
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, class_id, date, status, marked_by))
            conn.commit()
            conn.close()
            return True
        except:
            conn.close()
            return False
    
    def get_class_attendance(self, class_id, date):
        conn = self.db.get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT u.name, u.id, ca.roll_number, a.status, a.marked_at 
            FROM users u 
            JOIN class_assignments ca ON u.id = ca.user_id 
            LEFT JOIN attendance a ON u.id = a.user_id AND a.class_id = ? AND a.date = ?
            WHERE ca.class_id = ? AND ca.role = 'student'
            ORDER BY ca.roll_number
        ''', (class_id, date, class_id))
        attendance = cursor.fetchall()
        conn.close()
        return attendance
    
    def get_student_attendance(self, user_id, class_id=None):
        conn = self.db.get_db()
        cursor = conn.cursor()
        if class_id:
            cursor.execute('''
                SELECT a.*, c.name as class_name FROM attendance a 
                JOIN classes c ON a.class_id = c.id 
                WHERE a.user_id = ? AND a.class_id = ?
                ORDER BY a.date DESC
            ''', (user_id, class_id))
        else:
            cursor.execute('''
                SELECT a.*, c.name as class_name FROM attendance a 
                JOIN classes c ON a.class_id = c.id 
                WHERE a.user_id = ?
                ORDER BY a.date DESC
            ''', (user_id,))
        attendance = cursor.fetchall()
        conn.close()
        return attendance

class ClassRequest:
    def __init__(self, db):
        self.db = db
    
    def create_request(self, teacher_id, class_name, description):
        conn = self.db.get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO class_requests (teacher_id, class_name, description) 
            VALUES (?, ?, ?)
        ''', (teacher_id, class_name, description))
        conn.commit()
        request_id = cursor.lastrowid
        conn.close()
        return request_id
    
    def get_pending_requests(self):
        conn = self.db.get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT cr.*, u.name as teacher_name FROM class_requests cr 
            JOIN users u ON cr.teacher_id = u.id 
            WHERE cr.status = 'pending'
            ORDER BY cr.requested_at DESC
        ''')
        requests = cursor.fetchall()
        conn.close()
        return requests
    
    def approve_request(self, request_id, reviewed_by):
        conn = self.db.get_db()
        cursor = conn.cursor()
        
        # Get request details
        cursor.execute('SELECT * FROM class_requests WHERE id = ?', (request_id,))
        request = cursor.fetchone()
        
        if request:
            # Create the class
            cursor.execute('INSERT INTO classes (name, description) VALUES (?, ?)', 
                         (request['class_name'], request['description']))
            class_id = cursor.lastrowid
            
            # Assign teacher to class
            cursor.execute('''
                INSERT INTO class_assignments (user_id, class_id, role) 
                VALUES (?, ?, 'teacher')
            ''', (request['teacher_id'], class_id))
            
            # Update request status
            cursor.execute('''
                UPDATE class_requests 
                SET status = 'approved', reviewed_by = ?, reviewed_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (reviewed_by, request_id))
            
            conn.commit()
            conn.close()
            return True
        
        conn.close()
        return False
    
    def reject_request(self, request_id, reviewed_by):
        conn = self.db.get_db()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE class_requests 
            SET status = 'rejected', reviewed_by = ?, reviewed_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        ''', (reviewed_by, request_id))
        conn.commit()
        conn.close()
        return True
