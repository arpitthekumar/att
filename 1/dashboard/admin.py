from database import get_connection
from face_utils import capture_face

def register_teacher():
    import getpass
    print("\n--- Register Teacher ---")
    name = input("Name: ")
    email = input("Email: ")
    password = getpass.getpass("Password: ")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""INSERT INTO users (name, email, role, password) 
                   VALUES (?, ?, ?, ?)""", (name, email, "teacher", password))
    conn.commit()
    conn.close()
    print(f"✅ Teacher {name} registered successfully!\n")

def register_student():
    import getpass
    print("\n--- Register Student ---")
    name = input("Name: ")
    email = input("Email: ")
    password = getpass.getpass("Password: ")
    phone_number = input("Phone Number: ")
    parent_contact = input("Parent Contact: ")
    address = input("Address: ")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""INSERT INTO users 
                   (name, email, role, password, phone_number, parent_contact, address) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                   (name, email, "student", password, phone_number, parent_contact, address))
    student_id = cur.lastrowid
    conn.commit()
    conn.close()

    capture_face(name, student_id)

def view_users():
    print("\n--- View Users ---")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, email, role FROM users ORDER BY role")
    users = cur.fetchall()
    conn.close()

    if not users:
        print("No users found.\n")
        return

    print("\nUsers in system:")
    for uid, uname, email, role in users:
        print(f"ID: {uid} | Name: {uname} | Email: {email} | Role: {role}")
    print()


def view_classes():
    print("\n--- View Classes ---")
    conn = get_connection()
    cur = conn.cursor()

    # Get all classes with teacher
    cur.execute("""SELECT c.id, c.name, u.name 
                   FROM classes c 
                   LEFT JOIN users u ON c.teacher_id = u.id""")
    classes = cur.fetchall()

    if not classes:
        print("No classes created yet.\n")
        conn.close()
        return

    print(f"\nTotal Classes: {len(classes)}")
    for cid, cname, tname in classes:
        print(f"ID: {cid} | Class: {cname} | Teacher: {tname if tname else 'Not Assigned'}")

    see_details = input("\nDo you want to see details of a class? (y/n): ").lower()
    if see_details == "y":
        class_id = int(input("Enter Class ID: "))
        cur.execute("""SELECT c.name, u.name 
                       FROM classes c 
                       LEFT JOIN users u ON c.teacher_id = u.id 
                       WHERE c.id=?""", (class_id,))
        class_info = cur.fetchone()

        if not class_info:
            print("❌ Class not found.\n")
        else:
            cname, tname = class_info
            print(f"\n📘 Class: {cname}")
            print(f"👨‍🏫 Teacher: {tname if tname else 'Not Assigned'}")

            # Fetch students in this class
            cur.execute("""SELECT u.id, u.name 
                           FROM class_students cs
                           JOIN users u ON cs.student_id = u.id
                           WHERE cs.class_id=?""", (class_id,))
            students = cur.fetchall()

            print("\n👥 Students:")
            if students:
                for sid, sname in students:
                    print(f"- {sname} (ID: {sid})")
            else:
                print("No students assigned to this class.")

    conn.close()
    print()


def create_class():
    print("\n--- Create Class ---")
    name = input("Class Name: ")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM users WHERE role='teacher'")
    teachers = cur.fetchall()
    print("Available Teachers:")
    for tid, tname in teachers:
        print(f"{tid}: {tname}")

    teacher_id = int(input("Assign teacher (ID): "))
    cur.execute("INSERT INTO classes (name, teacher_id) VALUES (?, ?)", (name, teacher_id))
    conn.commit()
    conn.close()
    print(f"✅ Class {name} created successfully!\n")

def assign_student_to_class():
    print("\n--- Assign Student to Class ---")
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, name FROM users WHERE role='student'")
    students = cur.fetchall()
    print("Students:")
    for sid, sname in students:
        print(f"{sid}: {sname}")

    cur.execute("SELECT id, name FROM classes")
    classes = cur.fetchall()
    print("Classes:")
    for cid, cname in classes:
        print(f"{cid}: {cname}")

    student_id = int(input("Student ID: "))
    class_id = int(input("Class ID: "))

    cur.execute("INSERT INTO class_students (class_id, student_id) VALUES (?, ?)", (class_id, student_id))
    conn.commit()
    conn.close()
    print("✅ Student assigned successfully!\n")

def unassign_student_from_class():
    print("\n--- Unassign Student from Class ---")
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""SELECT cs.id, u.name, c.name 
                   FROM class_students cs
                   JOIN users u ON cs.student_id = u.id
                   JOIN classes c ON cs.class_id = c.id""")
    links = cur.fetchall()
    for lid, uname, cname in links:
        print(f"{lid}: {uname} → {cname}")

    link_id = int(input("Enter link ID to remove: "))
    cur.execute("DELETE FROM class_students WHERE id=?", (link_id,))
    conn.commit()
    conn.close()
    print("✅ Student unassigned successfully!\n")

def delete_user():
    print("\n--- Delete User ---")
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, name, role FROM users")
    users = cur.fetchall()
    for uid, uname, role in users:
        print(f"{uid}: {uname} ({role})")

    user_id = int(input("Enter user ID to delete: "))

    # Delete related records
    cur.execute("DELETE FROM face_encodings WHERE student_id=?", (user_id,))
    cur.execute("DELETE FROM class_students WHERE student_id=?", (user_id,))
    cur.execute("DELETE FROM attendance WHERE student_id=?", (user_id,))
    cur.execute("DELETE FROM classes WHERE teacher_id=?", (user_id,))
    cur.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
    print("✅ User deleted successfully!\n")

def delete_class():
    print("\n--- Delete Class ---")
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, name FROM classes")
    classes = cur.fetchall()
    for cid, cname in classes:
        print(f"{cid}: {cname}")

    class_id = int(input("Enter class ID to delete: "))

    # Delete related records
    cur.execute("DELETE FROM class_students WHERE class_id=?", (class_id,))
    cur.execute("DELETE FROM attendance WHERE class_id=?", (class_id,))
    cur.execute("DELETE FROM classes WHERE id=?", (class_id,))
    conn.commit()
    conn.close()
    print("✅ Class deleted successfully!\n")

def view_activities():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""SELECT a.id, u.name, a.activity, a.timestamp 
                   FROM activities a 
                   LEFT JOIN users u ON a.user_id = u.id 
                   ORDER BY a.timestamp DESC""")
    rows = cur.fetchall()
    conn.close()

    print("\n📜 Activities Log:")
    for row in rows:
        act_id, user_name, activity, ts = row
        uname = user_name if user_name else "Admin (demo)"
        print(f"[{ts}] {uname} → {activity}")
    print()

def view_all_attendance():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""SELECT c.name, u.name, a.date, a.status 
                   FROM attendance a
                   JOIN users u ON a.student_id = u.id
                   JOIN classes c ON a.class_id = c.id
                   ORDER BY a.date DESC""")
    rows = cur.fetchall()
    conn.close()

    print("\n📋 All Attendance Records:")
    for cname, uname, date, status in rows:
        print(f"{date} | {cname} | {uname} → {status}")
    print()

def admin_dashboard():
    while True:
        print("\n=== Admin Dashboard ===")
        print("1. Register Teacher\n2. Register Student\n3. Create Class\n4. Assign Student to Class")
        print("5. Unassign Student from Class\n6. Delete User\n7. Delete Class")
        print("8. View Activities\n9. View All Attendance")
        print("10. View Users\n11. View Classes")
        print("12. Logout")

        choice = input("Enter choice: ")
        if choice == "1":
            register_teacher()
        elif choice == "2":
            register_student()
        elif choice == "3":
            create_class()
        elif choice == "4":
            assign_student_to_class()
        elif choice == "5":
            unassign_student_from_class()
        elif choice == "6":
            delete_user()
        elif choice == "7":
            delete_class()
        elif choice == "8":
            view_activities()
        elif choice == "9":
            view_all_attendance()
        elif choice == "10":
            view_users()
        elif choice == "11":
            view_classes()
        elif choice == "12":
            print("👋 Logged out.\n")
            break
        else:
            print("❌ Invalid choice, try again.\n")