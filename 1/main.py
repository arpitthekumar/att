import getpass
from database import init_db, get_connection, log_activity
from dashboard.admin import admin_dashboard
from dashboard.teacher import teacher_dashboard
from dashboard.student import student_dashboard


# ====== DEMO ADMIN ======
users = {
    "admin": {"password": "admin123", "role": "admin"},
}

def login():
    print("\n=== Attendance System CLI ===")
    username = input("Username (email for DB users): ")
    password = getpass.getpass("Password: ")

    # Demo admin
    if username in users and users[username]["password"] == password:
        print("✅ Logged in as Admin (Demo Account)\n")
        log_activity(0, "Admin login (demo)")
        return (0, "admin")

    # DB users
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, role, password FROM users WHERE email=?", (username,))
    row = cur.fetchone()
    conn.close()

    if row:
        user_id, db_role, db_password = row
        if db_password == password:
            print(f"✅ Logged in as {db_role.capitalize()} (DB User)\n")
            log_activity(user_id, f"{db_role} login")
            return (user_id, db_role)

    print("❌ Invalid credentials\n")
    return None, None


def main():
    init_db()
    while True:
        user_id, role = None, None
        while not role:
            user_id, role = login()

        if role == "admin":
            admin_dashboard()
        elif role == "teacher":
            teacher_dashboard(user_id)
        elif role == "student":
            student_dashboard(user_id)


if __name__ == "__main__":
    main()
