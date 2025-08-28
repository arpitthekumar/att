from functools import wraps
from flask import session, redirect, url_for, flash, request
from werkzeug.security import check_password_hash
from datetime import datetime, timedelta
from .database import Database
from .models import User, UserActivity

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        # Check if session has expired (48 hours)
        if 'login_time' in session:
            login_time = datetime.fromisoformat(session['login_time'])
            if datetime.now() - login_time > timedelta(hours=48):
                session.clear()
                flash('Your session has expired. Please log in again.', 'info')
                return redirect(url_for('login'))
        
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        # Check if session has expired (48 hours)
        if 'login_time' in session:
            login_time = datetime.fromisoformat(session['login_time'])
            if datetime.now() - login_time > timedelta(hours=48):
                session.clear()
                flash('Your session has expired. Please log in again.', 'info')
                return redirect(url_for('login'))
        
        if session.get('role') != 'admin':
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        # Check if session has expired (48 hours)
        if 'login_time' in session:
            login_time = datetime.fromisoformat(session['login_time'])
            if datetime.now() - login_time > timedelta(hours=48):
                session.clear()
                flash('Your session has expired. Please log in again.', 'info')
                return redirect(url_for('login'))
        
        if session.get('role') not in ['admin', 'teacher']:
            flash('Access denied. Teacher privileges required.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        
        # Check if session has expired (48 hours)
        if 'login_time' in session:
            login_time = datetime.fromisoformat(session['login_time'])
            if datetime.now() - login_time > timedelta(hours=48):
                session.clear()
                flash('Your session has expired. Please log in again.', 'info')
                return redirect(url_for('login'))
        
        if session.get('role') not in ['admin', 'teacher', 'student']:
            flash('Access denied. Student privileges required.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def track_activity(activity_type='page_view'):
    """Decorator to track user activity"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Execute the original function
            result = f(*args, **kwargs)
            
            # Track activity if user is logged in
            if 'user_id' in session:
                try:
                    auth = Auth()
                    auth.log_activity(
                        user_id=session['user_id'],
                        activity_type=activity_type,
                        page_url=request.url,
                        ip_address=request.remote_addr,
                        user_agent=request.headers.get('User-Agent')
                    )
                except:
                    pass  # Don't break the app if activity tracking fails
            
            return result
        return decorated_function
    return decorator

class Auth:
    def __init__(self):
        self.db = Database()
        self.user_model = User(self.db)
        self.activity_model = UserActivity(self.db)
    
    def authenticate(self, username, password):
        user = self.user_model.get_by_username(username)
        if user and check_password_hash(user['password_hash'], password):
            return user
        return None
    
    def login_user(self, user):
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['name'] = user['name']
        session['role'] = user['role']
        session['email'] = user['email']
        session['login_time'] = datetime.now().isoformat()
        
        # Log login activity
        self.log_activity(
            user_id=user['id'],
            activity_type='login',
            page_url='/login',
            action_description='User logged in successfully'
        )
    
    def logout_user(self):
        if 'user_id' in session:
            # Log logout activity
            self.log_activity(
                user_id=session['user_id'],
                activity_type='logout',
                page_url='/logout',
                action_description='User logged out'
            )
        session.clear()
    
    def get_current_user(self):
        if 'user_id' in session:
            return self.user_model.get_by_id(session['user_id'])
        return None
    
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
    
    def get_user_activity(self, user_id, limit=50):
        """Get activity for a specific user"""
        return self.activity_model.get_user_activity(user_id, limit)
    
    def get_recent_activity(self, hours=24, role=None):
        """Get recent activity across all users or filtered by role"""
        return self.activity_model.get_recent_activity(hours, role)
    
    def get_active_users(self, hours=24):
        """Get list of active users in the last N hours"""
        return self.activity_model.get_active_users(hours)
    
    def is_admin(self):
        return session.get('role') == 'admin'
    
    def is_teacher(self):
        return session.get('role') in ['admin', 'teacher']
    
    def is_student(self):
        return session.get('role') in ['admin', 'teacher', 'student']
    
    def get_session_remaining_time(self):
        """Get remaining session time in hours"""
        if 'login_time' in session:
            login_time = datetime.fromisoformat(session['login_time'])
            elapsed = datetime.now() - login_time
            remaining = timedelta(hours=48) - elapsed
            return max(0, remaining.total_seconds() / 3600)  # Return hours
        return 0
