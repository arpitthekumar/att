import cv2
import face_recognition
import numpy as np
from database import save_encoding

def is_blurry(frame, threshold=100.0):
    """Detect blur using variance of Laplacian"""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var() < threshold

def capture_face(name, student_id):
    print(f"📸 Capturing face data for {name}...")
    cap = cv2.VideoCapture(1)

    # Angles to capture: 5 samples each
    angles = ["Center", "Left", "Right", "Up", "Down"]
    samples_per_angle = 4
    total_required = samples_per_angle * len(angles)

    face_encodings = []
    angle_index = 0
    count = 0

    while count < total_required:
        ret, frame = cap.read()
        if not ret:
            continue

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame)

        instruction = f"Look {angles[angle_index]} ({count % samples_per_angle + 1}/{samples_per_angle})"

        if face_locations:
            top, right, bottom, left = face_locations[0]
            face_w, face_h = right - left, bottom - top

            # Check face size
            if face_w < 100 or face_h < 100:
                cv2.putText(frame, "⚠️ Move closer", (20, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            elif is_blurry(frame):
                cv2.putText(frame, "⚠️ Hold still (blurry)", (20, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            else:
                face_encoding = face_recognition.face_encodings(rgb_frame, [face_locations[0]])[0]
                face_encodings.append(face_encoding)
                count += 1
                print(f"✅ {instruction} captured ({count}/{total_required})")

                if count % samples_per_angle == 0:
                    angle_index += 1  # move to next instruction

                cv2.putText(frame, f"Captured {count}/{total_required}", (20, 70),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            # Draw bounding box
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)

        # Always show instruction
        cv2.putText(frame, instruction, (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)

        cv2.imshow("Register Face", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

    if face_encodings:
        avg_encoding = np.mean(face_encodings, axis=0)
        save_encoding(student_id, avg_encoding)
        print(f"✅ {name}'s face saved with {len(face_encodings)} high-quality samples!\n")
    else:
        print("❌ No good face detected. Try again.\n")
