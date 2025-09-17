import cv2
import numpy as np
import sqlite3
from flask import Flask, render_template, request, jsonify, Response, send_file
from datetime import datetime
import os
import csv
from io import StringIO

app = Flask(__name__)
app.secret_key = "proximasecret"
DB_NAME = "attendance.db"

# ---------------- Database ----------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS employees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_name TEXT,
                    date TEXT,
                    time TEXT,
                    status TEXT,
                    FOREIGN KEY(employee_name) REFERENCES employees(name)
                )''')
    conn.commit()
    conn.close()

def mark_attendance(name, status):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    current_time = now.strftime("%H:%M:%S")

    c.execute("SELECT * FROM attendance WHERE employee_name=? AND date=?", (name, today))
    record = c.fetchone()

    if record is None:
        c.execute("INSERT INTO attendance (employee_name, date, time, status) VALUES (?, ?, ?, ?)",
                  (name, today, current_time, status))
    else:
        if status == "Out":
            c.execute("UPDATE attendance SET time=?, status=? WHERE employee_name=? AND date=?",
                      (current_time, status, name, today))

    conn.commit()
    conn.close()

# ---------------- Face Recognition ----------------
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

def gen_frames():
    cap = cv2.VideoCapture(0)
    while True:
        success, frame = cap.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

# ---------------- Routes ----------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/authenticate', methods=['POST'])
def authenticate():
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    if not os.path.exists("face_model.yml") or not os.path.exists("names.npy"):
        return jsonify({"name": None, "status": "Model not found", "confidence": None})

    recognizer.read("face_model.yml")
    names = np.load("names.npy", allow_pickle=True)

    cap = cv2.VideoCapture(0)
    recognized_name, status, confidence_value = None, None, None

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            id_, confidence = recognizer.predict(gray[y:y+h, x:x+w])
            if confidence < 50:
                recognized_name = names[id_]
                status = "In"
                confidence_value = 100 - confidence  # similarity %
                mark_attendance(recognized_name, status)
                cap.release()
                return jsonify({
                    "name": recognized_name,
                    "status": status,
                    "confidence": float(confidence_value)
                })
        break

    cap.release()
    return jsonify({"name": None, "status": "Unknown", "confidence": None})

@app.route('/attendance', methods=['GET', 'POST'])
def attendance():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    if request.method == 'POST':
        name = request.form.get('name')
        if name:
            try:
                c.execute("INSERT INTO employees (name) VALUES (?)", (name,))
                conn.commit()
            except sqlite3.IntegrityError:
                pass

    c.execute("SELECT * FROM employees")
    employees = c.fetchall()

    today = datetime.now().strftime("%Y-%m-%d")
    c.execute("SELECT * FROM attendance WHERE date=?", (today,))
    today_attendance = c.fetchall()

    conn.close()
    return render_template('attendance.html', employees=employees, today_attendance=today_attendance)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/export_csv')
def export_csv():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM attendance")
    rows = c.fetchall()
    conn.close()

    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(["ID", "Name", "Date", "Time", "Status"])
    writer.writerows(rows)
    output = si.getvalue()

    return Response(output, mimetype="text/csv",
                    headers={"Content-Disposition":"attachment;filename=attendance.csv"})

if __name__ == "__main__":
    init_db()
    app.run(debug=True)


