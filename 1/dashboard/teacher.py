from database import get_connection, load_encodings
import cv2, face_recognition
from datetime import datetime

def take_attendance(teacher_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM classes WHERE teacher_id=?", (teacher_id,))
    classes = cur.fetchall()
    if not classes:
        print("⚠️ No classes assigned!\n")
        return

    print("Your Classes:")
    for cid, cname in classes:
        print(f"{cid}: {cname}")

    class_id = int(input("Select class ID: "))

    cur.execute("""SELECT u.id, u.name 
                   FROM class_students cs
                   JOIN users u ON cs.student_id = u.id
                   WHERE cs.class_id=?""", (class_id,))
    students = cur.fetchall()
    if not students:
        print("⚠️ No students in this class!\n")
        return

    ids, encodings = load_encodings()
    print("📸 Starting Attendance... Press 'q' to stop.")
    cap = cv2.VideoCapture(1)
    present_ids = set()

    while True:
        ret, frame = cap.read()
        if not ret: continue

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encs = face_recognition.face_encodings(rgb_frame, face_locations)

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encs):
            matches = face_recognition.compare_faces(encodings, face_encoding, tolerance=0.5)
            name = "Unknown"

            if True in matches:
                idx = matches.index(True)
                student_id = ids[idx]
                if any(sid == student_id for sid, _ in students):
                    cur.execute("SELECT name FROM users WHERE id=?", (student_id,))
                    name = cur.fetchone()[0]
                    present_ids.add(student_id)

            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

        cv2.imshow("Attendance", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

    today = datetime.now().date().isoformat()
    for sid, sname in students:
        status = "Present" if sid in present_ids else "Absent"
        cur.execute("INSERT INTO attendance (class_id, student_id, date, status) VALUES (?, ?, ?, ?)",
                    (class_id, sid, today, status))

    conn.commit()
    conn.close()
    print("✅ Attendance saved!\n")

def view_teacher_attendance(teacher_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""SELECT c.name, u.name, a.date, a.status 
                   FROM attendance a
                   JOIN users u ON a.student_id = u.id
                   JOIN classes c ON a.class_id = c.id
                   WHERE c.teacher_id=?
                   ORDER BY a.date DESC""", (teacher_id,))
    rows = cur.fetchall()
    conn.close()

    print("\n📋 Your Classes Attendance Records:")
    for cname, uname, date, status in rows:
        print(f"{date} | {cname} | {uname} → {status}")
    print()

def teacher_dashboard(teacher_id):
    while True:
        print("\n=== Teacher Dashboard ===")
        print("1. Take Attendance\n2. View Attendance\n3. Logout")
        choice = input("Enter choice: ")
        if choice == "1":
            take_attendance(teacher_id)
        elif choice == "2":
            view_teacher_attendance(teacher_id)
        elif choice == "3":
            print("👋 Logged out.\n")
            break
