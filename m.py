import cv2
import os
from deepface import DeepFace
import pandas as pd
from datetime import datetime

# Paths
dataset_path = "dataset"   # Folder where registered faces will be stored
attendance_file = "attendance.xlsx"

# Create dataset folder if not exists
if not os.path.exists(dataset_path):
    os.makedirs(dataset_path)

# Initialize Excel file if not exists
if not os.path.exists(attendance_file):
    df = pd.DataFrame(columns=["Name", "Date", "Time"])
    df.to_excel(attendance_file, index=False)


# ---------------- FUNCTIONS -----------------

def register_student(name):
    """Capture and save a student's face"""
    cap = cv2.VideoCapture(0)
    print(f"Registering {name}... Press 'q' to capture and quit.")

    while True:
        ret, frame = cap.read()
        cv2.imshow("Register Face", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            filepath = os.path.join(dataset_path, f"{name}.jpg")
            cv2.imwrite(filepath, frame)
            print(f"✅ Face of {name} saved at {filepath}")
            break

    cap.release()
    cv2.destroyAllWindows()


def mark_attendance(name):
    """Mark attendance in Excel file"""
    df = pd.read_excel(attendance_file)
    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")

    if not ((df["Name"] == name) & (df["Date"] == date)).any():
        new_entry = pd.DataFrame([[name, date, time]], columns=["Name", "Date", "Time"])
        df = pd.concat([df, new_entry], ignore_index=True)
        df.to_excel(attendance_file, index=False)
        print(f"📌 Attendance marked for {name} at {time}")
    else:
        print(f"✔ {name} already marked today.")


def recognize_faces():
    """Recognize faces and mark attendance"""
    cap = cv2.VideoCapture(0)
    print("Recognition started... Press 'q' to quit.")

    while True:
        ret, frame = cap.read()
        cv2.imshow("Face Recognition", frame)

        for file in os.listdir(dataset_path):
            student_name = os.path.splitext(file)[0]
            student_path = os.path.join(dataset_path, file)

            try:
                result = DeepFace.verify(frame, student_path, enforce_detection=False)
                if result["verified"]:
                    mark_attendance(student_name)
                    cv2.putText(frame, f"{student_name}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX,
                                1, (0, 255, 0), 2, cv2.LINE_AA)
                    cv2.imshow("Face Recognition", frame)
            except:
                pass

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


def update_student(old_name, new_name=None):
    """Update student details (rename or recapture face)"""
    old_file = os.path.join(dataset_path, f"{old_name}.jpg")
    if not os.path.exists(old_file):
        print(f"❌ No student found with name {old_name}")
        return

    if new_name:  # Rename
        new_file = os.path.join(dataset_path, f"{new_name}.jpg")
        os.rename(old_file, new_file)
        print(f"✅ {old_name} renamed to {new_name}")
    else:  # Recapture
        os.remove(old_file)
        register_student(old_name)


def delete_student(name):
    """Delete student face data"""
    file = os.path.join(dataset_path, f"{name}.jpg")
    if os.path.exists(file):
        os.remove(file)
        print(f"🗑 Deleted {name}'s record.")
    else:
        print(f"❌ No student found with name {name}")


def view_attendance():
    """Display attendance records"""
    if os.path.exists(attendance_file):
        df = pd.read_excel(attendance_file)
        print("\n📖 Attendance Records:")
        print(df)
    else:
        print("❌ No attendance file found.")


# ---------------- MAIN MENU -----------------
while True:
    print("\n========= FACE RECOGNITION ATTENDANCE =========")
    print("1. Register Student")
    print("2. Start Attendance")
    print("3. Update Student (Rename or Recapture)")
    print("4. Delete Student")
    print("5. View Attendance Records")
    print("9. Exit")
    choice = input("Enter choice: ")

    if choice == "1":
        name = input("Enter student name: ")
        register_student(name)

    elif choice == "2":
        recognize_faces()

    elif choice == "3":
        old_name = input("Enter current student name: ")
        option = input("Type 'rename' to change name or 'recapture' to take new photo: ")
        if option.lower() == "rename":
            new_name = input("Enter new name: ")
            update_student(old_name, new_name=new_name)
        elif option.lower() == "recapture":
            update_student(old_name)

    elif choice == "4":
        name = input("Enter student name to delete: ")
        delete_student(name)

    elif choice == "5":
        view_attendance()

    elif choice == "9":
        print("👋 Exiting program. Goodbye!")
        break

    else:
        print("❌ Invalid choice, try again.")
