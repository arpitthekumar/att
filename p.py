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

    # Check if already marked today
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

        # Loop over registered students
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

# ---------------- MAIN -----------------
print("Options:\n1. Register Student\n2. Start Attendance")
choice = input("Enter choice: ")

if choice == "1":
    name = input("Enter student name: ")
    register_student(name)

elif choice == "2":
    recognize_faces()
