import os
import pickle
import cv2
import face_recognition
import getpass

# File to store students and face encodings
STUDENT_FILE = "students.pkl"

# Load existing students
if os.path.exists(STUDENT_FILE):
    with open(STUDENT_FILE, "rb") as f:
        students = pickle.load(f)
else:
    students = {}

# ====== LOGIN SYSTEM ======
users = {
    "admin": {"password": "admin123", "role": "admin"},
    "teacher": {"password": "teach123", "role": "teacher"},
    "student": {"password": "stud123", "role": "student"},
}


def login():
    print("\n=== Attendance System CLI ===")
    username = input("Username: ")
    password = getpass.getpass("Password: ")

    if username in users and users[username]["password"] == password:
        print(f"✅ Logged in as {users[username]['role'].capitalize()}\n")
        return users[username]["role"]
    else:
        print("❌ Invalid credentials\n")
        return None


# ====== ADD STUDENT WITH FACE CAPTURE ======
def add_student():
    name = input("Enter student name: ")
    print("📸 Opening camera... Please look straight, left, right, and up.")
    cap = cv2.VideoCapture(0)

    face_encodings = []
    count = 0

    while count < 5:  # Capture 5 images
        ret, frame = cap.read()
        if not ret:
            continue

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)

        if face_locations:
            face_encoding = face_recognition.face_encodings(rgb_frame, face_locations)[0]
            face_encodings.append(face_encoding)
            count += 1
            print(f"✅ Captured {count}/5 images")

            # Draw rectangle
            top, right, bottom, left = face_locations[0]
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)

        cv2.imshow("Register Face", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    if face_encodings:
        students[name] = face_encodings
        with open(STUDENT_FILE, "wb") as f:
            pickle.dump(students, f)
        print(f"✅ {name} added successfully with face data!\n")
    else:
        print("❌ No face detected. Try again.\n")


# ====== TAKE ATTENDANCE ======
def take_attendance():
    if not students:
        print("⚠️ No students registered yet!\n")
        return

    print("📸 Starting Attendance... Press 'q' to stop.")
    cap = cv2.VideoCapture(0)

    attendance = set()

    known_encodings = []
    known_names = []

    for name, encodings in students.items():
        for enc in encodings:
            known_encodings.append(enc)
            known_names.append(name)

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            matches = face_recognition.compare_faces(known_encodings, face_encoding)
            name = "Unknown"

            if True in matches:
                first_match_index = matches.index(True)
                name = known_names[first_match_index]
                attendance.add(name)

            # Draw rectangle & name
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(frame, name, (left, top - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

        cv2.imshow("Attendance", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    print("\n📋 Attendance Recorded:")
    for student in attendance:
        print(f"✅ {student} - Present")

    print("🔒 Attendance session closed.\n")


# ====== MAIN MENU ======
def main():
    while True:
        role = login()
        if not role:
            continue

        if role == "admin":
            print("1. Add Student\n2. Logout")
            choice = input("Enter choice: ")
            if choice == "1":
                add_student()
            elif choice == "2":
                continue

        elif role == "teacher":
            print("1. Take Attendance\n2. Logout")
            choice = input("Enter choice: ")
            if choice == "1":
                take_attendance()
            elif choice == "2":
                continue

        elif role == "student":
            print("📌 Students can only view attendance (future feature).")
            continue


if __name__ == "__main__":
    main()
