import sqlite3
import numpy as np

DB_FILE = "school.db"

def get_connection():
    return sqlite3.connect(DB_FILE)

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # Users
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        role TEXT,
        password TEXT,
        phone_number TEXT,
        parent_contact TEXT,
        address TEXT
    )''')

    # Classes
    cur.execute('''CREATE TABLE IF NOT EXISTS classes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        teacher_id INTEGER,
        FOREIGN KEY (teacher_id) REFERENCES users(id)
    )''')

    # Class-Students junction
    cur.execute('''CREATE TABLE IF NOT EXISTS class_students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        class_id INTEGER,
        student_id INTEGER,
        FOREIGN KEY (class_id) REFERENCES classes(id),
        FOREIGN KEY (student_id) REFERENCES users(id)
    )''')

    # Attendance
    cur.execute('''CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        class_id INTEGER,
        student_id INTEGER,
        date TEXT,
        status TEXT,
        FOREIGN KEY (class_id) REFERENCES classes(id),
        FOREIGN KEY (student_id) REFERENCES users(id)
    )''')

    # Activities
    cur.execute('''CREATE TABLE IF NOT EXISTS activities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        activity TEXT,
        timestamp TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')

    # Face Encodings
    cur.execute('''CREATE TABLE IF NOT EXISTS face_encodings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER,
        encoding BLOB,
        FOREIGN KEY (student_id) REFERENCES users(id)
    )''')

    conn.commit()
    conn.close()

# Helper functions for vectors
def save_encoding(student_id, encoding: np.ndarray):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO face_encodings (student_id, encoding) VALUES (?, ?)",
                (student_id, encoding.astype(np.float32).tobytes()))
    conn.commit()
    conn.close()

def load_encodings():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT student_id, encoding FROM face_encodings")
    rows = cur.fetchall()
    conn.close()

    encodings, ids = [], []
    for sid, blob in rows:
        encodings.append(np.frombuffer(blob, dtype=np.float32))
        ids.append(sid)
    return ids, encodings
def log_activity(user_id, activity):
    from datetime import datetime
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO activities (user_id, activity, timestamp) VALUES (?, ?, ?)",
                (user_id, activity, datetime.now().isoformat()))
    conn.commit()
    conn.close()