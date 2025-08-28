from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import cv2
from deepface import DeepFace
import pandas as pd
from datetime import datetime

app = Flask(__name__)

# Attendance file
attendance_file = "attendance.xlsx"
if not os.path.exists(attendance_file):
    df = pd.DataFrame(columns=["Name", "Date", "Time"])
    df.to_excel(attendance_file, index=False)

# Folder to store student faces
faces_dir = "faces"
os.makedirs(faces_dir, exist_ok=True)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["POST"])
def register():
    name = request.form["name"]

    # Open webcam for registration
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    if ret:
        path = os.path.join(faces_dir, f"{name}.jpg")
        cv2.imwrite(path, frame)
    cap.release()

    return redirect(url_for("index"))


@app.route("/attendance", methods=["POST"])
def attendance():
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    if not ret:
        return jsonify({"status": "error", "message": "Camera error"})

    recognized = False
    for img in os.listdir(faces_dir):
        db_path = os.path.join(faces_dir, img)
        try:
            result = DeepFace.verify(frame, db_path, model_name="VGG-Face")
            if result["verified"]:
                name = os.path.splitext(img)[0]
                now = datetime.now()
                df = pd.read_excel(attendance_file)
                df = pd.concat(
                    [
                        df,
                        pd.DataFrame([[name, now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S")]],
                                     columns=["Name", "Date", "Time"])
                    ],
                    ignore_index=True
                )
                df.to_excel(attendance_file, index=False)
                recognized = True
                break
        except Exception as e:
            print("Error:", e)

    cap.release()
    if recognized:
        return jsonify({"status": "success", "message": f"Attendance marked for {name}"})
    else:
        return jsonify({"status": "error", "message": "Face not recognized"})


@app.route("/records")
def records():
    df = pd.read_excel(attendance_file)
    return df.to_html(classes="table table-striped")


if __name__ == "__main__":
    app.run(debug=True)
