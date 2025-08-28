import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash

class Database:
    def __init__(self, db_path='attendance.db'):
        self.db_path = db_path
    
    def get_db(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def migrate_database(self):
        """Safely migrate existing database to new schema"""
        conn = self.get_db()
        cursor = conn.cursor()
        
        try:
            # Check if users table exists and has 'name' column
            cursor.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Add 'name' column to users table if it doesn't exist
            if 'name' not in columns:
                print("Adding 'name' column to users table...")
                cursor.execute('ALTER TABLE users ADD COLUMN name TEXT')
                
                # Update existing users with default names
                cursor.execute('UPDATE users SET name = username WHERE name IS NULL')
            
            # Check and update attendance table
            cursor.execute("PRAGMA table_info(attendance)")
            attendance_columns = [column[1] for column in cursor.fetchall()]
            
            # Add missing columns to attendance table
            if 'status' not in attendance_columns:
                print("Adding 'status' column to attendance table...")
                cursor.execute('ALTER TABLE attendance ADD COLUMN status TEXT DEFAULT "present"')
            
            if 'marked_by' not in attendance_columns:
                print("Adding 'marked_by' column to attendance table...")
                cursor.execute('ALTER TABLE attendance ADD COLUMN marked_by INTEGER')
            
            if 'marked_at' not in attendance_columns:
                print("Adding 'marked_at' column to attendance table...")
                cursor.execute('ALTER TABLE attendance ADD COLUMN marked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
                
            if 'remarks' not in attendance_columns:
                print("Adding 'remarks' column to attendance table...")
                cursor.execute('ALTER TABLE attendance ADD COLUMN remarks TEXT')
                
            if 'attendance_type' not in attendance_columns:
                print("Adding 'attendance_type' column to attendance table...")
                cursor.execute('ALTER TABLE attendance ADD COLUMN attendance_type TEXT DEFAULT "regular"')
            
            # Check and update class_assignments table
            cursor.execute("PRAGMA table_info(class_assignments)")
            assignment_columns = [column[1] for column in cursor.fetchall()]
            
            if 'roll_number' not in assignment_columns:
                print("Adding 'roll_number' column to class_assignments table...")
                cursor.execute('ALTER TABLE class_assignments ADD COLUMN roll_number TEXT')
            
            if 'assigned_at' not in assignment_columns:
                print("Adding 'assigned_at' column to class_assignments table...")
                cursor.execute('ALTER TABLE class_assignments ADD COLUMN assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
            
            # Check and update classes table
            cursor.execute("PRAGMA table_info(classes)")
            classes_columns = [column[1] for column in cursor.fetchall()]
            
            if 'description' not in classes_columns:
                print("Adding 'description' column to classes table...")
                cursor.execute('ALTER TABLE classes ADD COLUMN description TEXT')
            
            if 'created_at' not in classes_columns:
                print("Adding 'created_at' column to classes table...")
                cursor.execute('ALTER TABLE classes ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
            
            # Check and update students table
            cursor.execute("PRAGMA table_info(students)")
            students_columns = [column[1] for column in cursor.fetchall()]
            
            if 'face_image' not in students_columns:
                print("Adding 'face_image' column to students table...")
                cursor.execute('ALTER TABLE students ADD COLUMN face_image TEXT')
            
            if 'created_at' not in students_columns:
                print("Adding 'created_at' column to students table...")
                cursor.execute('ALTER TABLE students ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
            
            # Check if user_activity table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_activity'")
            if not cursor.fetchone():
                print("Creating user_activity table...")
                cursor.execute('''
                    CREATE TABLE user_activity (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        activity_type TEXT NOT NULL,
                        page_url TEXT,
                        action_description TEXT,
                        ip_address TEXT,
                        user_agent TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                ''')
            
            # Check if class_requests table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='class_requests'")
            if not cursor.fetchone():
                print("Creating class_requests table...")
                cursor.execute('''
                    CREATE TABLE class_requests (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        teacher_id INTEGER NOT NULL,
                        class_name TEXT NOT NULL,
                        description TEXT,
                        status TEXT DEFAULT 'pending',
                        requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        reviewed_by INTEGER,
                        reviewed_at TIMESTAMP,
                        FOREIGN KEY (teacher_id) REFERENCES users (id),
                        FOREIGN KEY (reviewed_by) REFERENCES users (id)
                    )
                ''')
            
            conn.commit()
            print("Database migration completed successfully!")
            
        except Exception as e:
            print(f"Migration error: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def init_db(self):
        conn = self.get_db()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'student',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Classes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS classes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Class assignments (many-to-many between users and classes)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS class_assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                class_id INTEGER NOT NULL,
                role TEXT NOT NULL, -- 'teacher' or 'student'
                roll_number TEXT, -- for students
                assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (class_id) REFERENCES classes (id),
                UNIQUE(user_id, class_id, role)
            )
        ''')
        
        # Students table (for additional student info)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                face_image TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Attendance table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                class_id INTEGER NOT NULL,
                date DATE NOT NULL,
                status TEXT DEFAULT 'present',
                marked_by INTEGER NOT NULL,
                marked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                remarks TEXT,
                attendance_type TEXT DEFAULT 'regular',
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (class_id) REFERENCES classes (id),
                FOREIGN KEY (marked_by) REFERENCES users (id),
                UNIQUE(user_id, class_id, date)
            )
        ''')
        
        # Class requests table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS class_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                teacher_id INTEGER NOT NULL,
                class_name TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'pending', -- 'pending', 'approved', 'rejected'
                requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reviewed_by INTEGER,
                reviewed_at TIMESTAMP,
                FOREIGN KEY (teacher_id) REFERENCES users (id),
                FOREIGN KEY (reviewed_by) REFERENCES users (id)
            )
        ''')
        
        # User activity tracking table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                activity_type TEXT NOT NULL, -- 'login', 'logout', 'page_view', 'action'
                page_url TEXT,
                action_description TEXT,
                ip_address TEXT,
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Run migration to update existing database
        self.migrate_database()
        
        # Insert default data only if it doesn't exist
        try:
            # Check if admin user exists
            cursor.execute('SELECT COUNT(*) FROM users WHERE username = ?', ('admin',))
            admin_exists = cursor.fetchone()[0] > 0
            
            if not admin_exists:
                print("Adding default users...")
                # Default admin user
                cursor.execute('''
                    INSERT INTO users (username, password_hash, email, name, role) 
                    VALUES (?, ?, ?, ?, ?)
                ''', ('admin', generate_password_hash('admin123'), 'admin@school.com', 'Administrator', 'admin'))
                
                # Default teacher
                cursor.execute('''
                    INSERT INTO users (username, password_hash, email, name, role) 
                    VALUES (?, ?, ?, ?, ?)
                ''', ('teacher1', generate_password_hash('teacher123'), 'teacher1@school.com', 'John Teacher', 'teacher'))
                
                # Default student
                cursor.execute('''
                    INSERT INTO users (username, password_hash, email, name, role) 
                    VALUES (?, ?, ?, ?, ?)
                ''', ('student1', generate_password_hash('student123'), 'student1@school.com', 'Alice Student', 'student'))
                
                # Default class
                cursor.execute('''
                    INSERT INTO classes (name, description) 
                    VALUES (?, ?)
                ''', ('Class 10A', 'Mathematics and Science'))
                
                # Get the IDs
                class_id = cursor.lastrowid
                
                # Assign teacher to class
                cursor.execute('''
                    INSERT INTO class_assignments (user_id, class_id, role) 
                    VALUES (?, ?, ?)
                ''', (2, class_id, 'teacher'))  # teacher1 has id 2
                
                # Assign student to class
                cursor.execute('''
                    INSERT INTO class_assignments (user_id, class_id, role, roll_number) 
                    VALUES (?, ?, ?, ?)
                ''', (3, class_id, 'student', '001'))  # student1 has id 3
                
                # Add student face data
                cursor.execute('''
                    INSERT INTO students (user_id) 
                    VALUES (?)
                ''', (3,))
                
                print("Default data added successfully!")
            else:
                print("Default users already exist, skipping...")
            
        except sqlite3.IntegrityError as e:
            print(f"Data already exists: {e}")
        except Exception as e:
            print(f"Error adding default data: {e}")
        
        conn.commit()
        conn.close()
