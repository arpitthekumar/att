from database import get_connection

def view_student_attendance(student_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""SELECT c.name, a.date, a.status 
                   FROM attendance a
                   JOIN classes c ON a.class_id = c.id
                   WHERE a.student_id=?
                   ORDER BY a.date DESC""", (student_id,))
    rows = cur.fetchall()
    conn.close()

    print("\n📋 Your Attendance Records:")
    for cname, date, status in rows:
        print(f"{date} | {cname} → {status}")
    print()

def student_dashboard(student_id):
    while True:
        print("\n=== Student Dashboard ===")
        print("1. View My Attendance\n2. Logout")
        choice = input("Enter choice: ")
        if choice == "1":
            view_student_attendance(student_id)
        elif choice == "2":
            print("👋 Logged out.\n")
            break
