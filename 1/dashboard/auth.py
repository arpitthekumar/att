import getpass
from database import get_connection, log_activity

# ====== DEMO ADMIN ======
demo_users = {
    "admin": {"password": "admin123", "role": "admin"},
}


def login():
    print("\n=== Attendance System CLI ===")
    username = input("Username (email for DB users): ")
    password = getpass.getpass("Password: ")

    # Demo admin login
    if username in demo_users and demo_users[username]["password"] == password:
        print("✅ Logged in as Admin (Demo Account)\n")
        log_activity(0, "Admin login (demo)")
        return (0, "admin")

    # DB users login
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
