"""
FaceSense - Flask API for student/staff registration, face + location, attendance.
New schema: students, staff, departments, degrees; ID card upload; semester face updates.
"""
import os
import base64
import json
import uuid
import cv2
import numpy as np
import pymysql
from datetime import datetime, date, timedelta
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS

from config import (
    DATASET_DIR,
    MODELS_DIR,
    MODEL_PATH,
    LABELS_PATH,
    EXPORTS_DIR,
    UPLOADS_DIR,
    ALLOWED_EXTENSIONS,
    CONFIDENCE_THRESHOLD,
    LOCATION_ACCURACY_THRESHOLD,
    FRONTEND_BUILD_DIR,
)
from db import get_connection
from utils.location_utils import is_near_registered_location, is_within_campus
from export_utils import export_to_excel, get_students_attendance_for_export, get_staff_attendance_for_export

app = Flask(__name__)
CORS(app, supports_credentials=True)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB for ID card

_recognizer = None
_id_to_name = None


@app.route("/", methods=["GET"])
def index():
    """Serve built React frontend index if available, else show backend message."""
    index_path = os.path.join(FRONTEND_BUILD_DIR, "index.html")
    if os.path.isfile(index_path):
        # Serve built SPA
        return send_from_directory(FRONTEND_BUILD_DIR, "index.html")
    # Fallback message if frontend is not built
    return (
        "<!doctype html>"
        "<html><head><title>FaceSense Backend</title></head>"
        "<body>"
        "<h1>FaceSense Backend Running</h1>"
        "<p>API is available under the <code>/api</code> paths.</p>"
        "<p>Build frontend with <code>npm run build</code> to serve the full UI here.</p>"
        "</body></html>"
    )


@app.route("/assets/<path:filename>", methods=["GET"])
def frontend_assets(filename):
    """Serve static assets from built React frontend."""
    assets_dir = os.path.join(FRONTEND_BUILD_DIR, "assets")
    return send_from_directory(assets_dir, filename)


def get_recognizer():
    global _recognizer, _id_to_name
    if _recognizer is None and os.path.isfile(MODEL_PATH) and os.path.isfile(LABELS_PATH):
        _recognizer = cv2.face.LBPHFaceRecognizer_create()
        _recognizer.read(MODEL_PATH)
        with open(LABELS_PATH, "r") as f:
            meta = json.load(f)
            _id_to_name = {int(k): v for k, v in meta.get("id_to_name", {}).items()}
    return _recognizer, _id_to_name


def invalidate_recognizer():
    global _recognizer, _id_to_name
    _recognizer = None
    _id_to_name = None


def get_face_detector():
    path = os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
    return cv2.CascadeClassifier(path)


def get_display_name(conn, user_id):
    with conn.cursor() as cur:
        cur.execute("SELECT first_name, last_name FROM students WHERE user_id = %s", (user_id,))
        row = cur.fetchone()
    if row:
        return f"{row.get('first_name') or ''} {row.get('last_name') or ''}".strip()
    with conn.cursor() as cur:
        cur.execute("SELECT first_name, last_name FROM staff WHERE user_id = %s", (user_id,))
        row = cur.fetchone()
    if row:
        return f"{row.get('first_name') or ''} {row.get('last_name') or ''}".strip()
    return str(user_id)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# ---------- Auth ----------
@app.route("/api/login", methods=["POST"])
def login():
    data = request.json or {}
    email = data.get("email", "").strip()
    password = data.get("password", "")
    if not email:
        return jsonify({"error": "Email required"}), 400
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, email, password_hash, role FROM users WHERE email = %s AND is_active = 1",
                (email,),
            )
            row = cur.fetchone()
    if not row:
        return jsonify({"error": "Invalid credentials"}), 401
    stored = row.get("password_hash") or ""
    if stored and stored != password:
        return jsonify({"error": "Invalid credentials"}), 401
    user = {"id": row["id"], "email": row["email"], "role": row["role"]}
    if row["role"] == "admin":
        user["name"] = "Administrator"
    else:
        with get_connection() as conn:
            name = get_display_name(conn, row["id"])
            user["name"] = name or email
    return jsonify({"user": user, "token": str(user["id"])})


# ---------- Departments ----------
@app.route("/api/departments", methods=["GET"])
def list_departments():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name FROM departments ORDER BY name")
            rows = cur.fetchall()
    return jsonify({"departments": rows})


@app.route("/api/departments", methods=["POST"])
def create_department():
    data = request.json or {}
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "Name required"}), 400
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO departments (name) VALUES (%s)", (name,))
                return jsonify({"id": cur.lastrowid, "name": name})
    except pymysql.IntegrityError:
        return jsonify({"error": "Department exists"}), 400


# ---------- Degrees ----------
@app.route("/api/degrees", methods=["GET"])
def list_degrees():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name FROM degrees ORDER BY name")
            rows = cur.fetchall()
    return jsonify({"degrees": rows})


@app.route("/api/degrees", methods=["POST"])
def create_degree():
    data = request.json or {}
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "Name required"}), 400
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO degrees (name) VALUES (%s)", (name,))
                return jsonify({"id": cur.lastrowid, "name": name})
    except pymysql.IntegrityError:
        return jsonify({"error": "Degree exists"}), 400


# ---------- Upload ID card ----------
@app.route("/api/upload-id-card", methods=["POST"])
def upload_id_card():
    if "file" not in request.files:
        return jsonify({"error": "No file"}), 400
    f = request.files["file"]
    if f.filename == "" or not allowed_file(f.filename):
        return jsonify({"error": "Invalid file"}), 400
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    ext = f.filename.rsplit(".", 1)[1].lower()
    filename = f"id_{uuid.uuid4().hex[:12]}.{ext}"
    path = os.path.join(UPLOADS_DIR, filename)
    f.save(path)
    return jsonify({"path": f"uploads/{filename}", "filename": filename})


# ---------- Student registration ----------
@app.route("/api/students/register", methods=["POST"])
def register_student():
    data = request.json or {}
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""
    first_name = (data.get("first_name") or "").strip()
    last_name = (data.get("last_name") or "").strip()
    if not email or not first_name or not last_name:
        return jsonify({"error": "Email, first name, last name required"}), 400
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (email, password_hash, role) VALUES (%s, %s, 'student')",
                    (email, password),
                )
                uid = cur.lastrowid
                cur.execute(
                    """INSERT INTO students (user_id, first_name, last_name, father_name, mother_name, phone, email,
                       parents_number, id_card_path, hair_colour, eye_colour, blood_group, year_of_study, semester,
                       department_id, degree_id, hod_name, class_teacher_id, shift_type, shift_time,
                       accept_rules, accept_face_recognition, location_permission) VALUES
                       (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (
                        uid,
                        first_name,
                        last_name,
                        data.get("father_name"),
                        data.get("mother_name"),
                        data.get("phone"),
                        email,
                        data.get("parents_number"),
                        data.get("id_card_path"),
                        data.get("hair_colour"),
                        data.get("eye_colour"),
                        data.get("blood_group"),
                        data.get("year_of_study"),
                        data.get("semester"),
                        data.get("department_id"),
                        data.get("degree_id"),
                        data.get("hod_name"),
                        data.get("class_teacher_id"),
                        data.get("shift_type"),
                        data.get("shift_time"),
                        1 if data.get("accept_rules") else 0,
                        1 if data.get("accept_face_recognition") else 0,
                        1 if data.get("location_permission") else 0,
                    ),
                )
        return jsonify({"id": uid, "user_id": uid, "email": email, "role": "student"})
    except pymysql.IntegrityError:
        return jsonify({"error": "Email already exists"}), 400


# ---------- Staff registration ----------
@app.route("/api/staff/register", methods=["POST"])
def register_staff():
    data = request.json or {}
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""
    first_name = (data.get("first_name") or "").strip()
    last_name = (data.get("last_name") or "").strip()
    if not email or not first_name or not last_name:
        return jsonify({"error": "Email, first name, last name required"}), 400
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (email, password_hash, role) VALUES (%s, %s, 'staff')",
                    (email, password),
                )
                uid = cur.lastrowid
                cur.execute(
                    """INSERT INTO staff (user_id, first_name, last_name, father_name, mother_or_spouse_name, phone, email,
                       marital_status, parents_or_spouse_number, id_card_path, hair_colour, eye_colour, blood_group,
                       degree_completed, department_id, hod_name, accept_rules, accept_face_recognition, location_permission)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (
                        uid,
                        first_name,
                        last_name,
                        data.get("father_name"),
                        data.get("mother_or_spouse_name"),
                        data.get("phone"),
                        email,
                        data.get("marital_status"),
                        data.get("parents_or_spouse_number"),
                        data.get("id_card_path"),
                        data.get("hair_colour"),
                        data.get("eye_colour"),
                        data.get("blood_group"),
                        data.get("degree_completed"),
                        data.get("department_id"),
                        data.get("hod_name"),
                        1 if data.get("accept_rules") else 0,
                        1 if data.get("accept_face_recognition") else 0,
                        1 if data.get("location_permission") else 0,
                    ),
                )
        return jsonify({"id": uid, "user_id": uid, "email": email, "role": "staff"})
    except pymysql.IntegrityError:
        return jsonify({"error": "Email already exists"}), 400


# ---------- Students list (admin: all; class_teacher: assigned) ----------
@app.route("/api/students", methods=["GET"])
def list_students():
    role = request.args.get("role")
    user_id = request.args.get("user_id", type=int)
    degree_id = request.args.get("degree_id", type=int)
    department_id = request.args.get("department_id", type=int)
    year = request.args.get("year", type=int)
    semester = request.args.get("semester", type=int)
    q = """SELECT s.*, d.name as department_name, deg.name as degree_name,
            CONCAT(st.first_name, ' ', st.last_name) as class_teacher_name
            FROM students s
            LEFT JOIN departments d ON d.id = s.department_id
            LEFT JOIN degrees deg ON deg.id = s.degree_id
            LEFT JOIN staff st ON st.user_id = s.class_teacher_id
            WHERE 1=1"""
    params = []
    if role == "class_teacher" and user_id:
        q += " AND s.class_teacher_id = %s"
        params.append(user_id)
    if degree_id:
        q += " AND s.degree_id = %s"
        params.append(degree_id)
    if department_id:
        q += " AND s.department_id = %s"
        params.append(department_id)
    if year is not None:
        q += " AND s.year_of_study = %s"
        params.append(year)
    if semester is not None:
        q += " AND s.semester = %s"
        params.append(semester)
    q += " ORDER BY s.first_name, s.last_name"
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(q, params)
            rows = cur.fetchall()
    return jsonify({"students": rows})


# ---------- Staff list (admin) ----------
@app.route("/api/staff", methods=["GET"])
def list_staff():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT s.*, d.name as department_name FROM staff s
                LEFT JOIN departments d ON d.id = s.department_id
                ORDER BY s.first_name, s.last_name
            """)
            rows = cur.fetchall()
    return jsonify({"staff": rows})


# ---------- Update student (semester, class_teacher, etc.) ----------
@app.route("/api/students/<int:user_id>", methods=["PATCH"])
def update_student(user_id):
    data = request.json or {}
    allowed = ("first_name", "last_name", "father_name", "mother_name", "phone", "email", "parents_number",
               "id_card_path", "hair_colour", "eye_colour", "blood_group", "year_of_study", "semester",
               "department_id", "degree_id", "hod_name", "class_teacher_id", "shift_type", "shift_time")
    updates = []
    params = []
    for k in allowed:
        if k in data:
            updates.append(f"{k} = %s")
            params.append(data[k])
    if not updates:
        return jsonify({"error": "No fields to update"}), 400
    params.append(user_id)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE students SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP WHERE user_id = %s",
                params,
            )
    return jsonify({"ok": True})


# ---------- Update staff ----------
@app.route("/api/staff/<int:user_id>", methods=["PATCH"])
def update_staff(user_id):
    data = request.json or {}
    allowed = ("first_name", "last_name", "father_name", "mother_or_spouse_name", "phone", "email",
               "marital_status", "parents_or_spouse_number", "id_card_path", "hair_colour", "eye_colour",
               "blood_group", "degree_completed", "department_id", "hod_name")
    updates = []
    params = []
    for k in allowed:
        if k in data:
            updates.append(f"{k} = %s")
            params.append(data[k])
    if not updates:
        return jsonify({"error": "No fields to update"}), 400
    params.append(user_id)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE staff SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP WHERE user_id = %s",
                params,
            )
    return jsonify({"ok": True})


# ---------- Admin: set student's class teacher ----------
@app.route("/api/students/<int:user_id>/class-teacher", methods=["PUT"])
def set_student_class_teacher(user_id):
    data = request.json or {}
    class_teacher_id = data.get("class_teacher_id")
    if class_teacher_id == "":
        class_teacher_id = None
    elif class_teacher_id is not None:
        try:
            class_teacher_id = int(class_teacher_id)
        except (TypeError, ValueError):
            return jsonify({"error": "Invalid class_teacher_id"}), 400
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE students SET class_teacher_id = %s, updated_at = CURRENT_TIMESTAMP WHERE user_id = %s", (class_teacher_id, user_id))
    return jsonify({"ok": True})


# ---------- Face registration ----------
@app.route("/api/register-face", methods=["POST"])
def register_face():
    data = request.json or {}
    user_id = data.get("user_id")
    image_b64 = data.get("image")
    lat = data.get("latitude")
    lon = data.get("longitude")
    if not user_id or not image_b64:
        return jsonify({"error": "user_id and image required"}), 400
    with get_connection() as conn:
        display_name = get_display_name(conn, user_id)
        if not display_name:
            return jsonify({"error": "User not found"}), 404
    user_dir = os.path.join(DATASET_DIR, str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    try:
        img_data = base64.b64decode(image_b64.split(",")[-1] if "," in image_b64 else image_b64)
        img = cv2.imdecode(np.frombuffer(img_data, np.uint8), cv2.IMREAD_GRAYSCALE)
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    if img is None:
        return jsonify({"error": "Invalid image"}), 400
    cascade = get_face_detector()
    faces = cascade.detectMultiScale(img, scaleFactor=1.2, minNeighbors=5, minSize=(80, 80))
    if len(faces) == 0:
        return jsonify({"error": "No face detected", "captured": False}), 400
    x, y, w, h = faces[0]
    face_roi = cv2.resize(img[y:y+h, x:x+w], (200, 200))
    count = len([f for f in os.listdir(user_dir) if f.lower().endswith((".jpg", ".png", ".jpeg"))])
    path = os.path.join(user_dir, f"{display_name.replace(' ', '_')}_{count+1:03d}.jpg")
    cv2.imwrite(path, face_roi)
    if count == 0 and lat is not None and lon is not None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO user_locations (user_id, latitude, longitude, registered_at) VALUES (%s, %s, %s, %s)",
                    (user_id, lat, lon, datetime.utcnow().isoformat()),
                )
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO face_registry (user_id, face_encoding_path, samples_count, registered_at)
                   VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE face_encoding_path = VALUES(face_encoding_path),
                   samples_count = VALUES(samples_count), registered_at = VALUES(registered_at)""",
                (user_id, f"dataset/{user_id}", count + 1, datetime.utcnow().isoformat()),
            )
            cur.execute(
                "UPDATE students SET semester_face_updated_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE user_id = %s",
                (user_id,),
            )
    return jsonify({"ok": True, "samples": count + 1, "location_saved": count == 0 and lat is not None})


# ---------- Train model ----------
@app.route("/api/train", methods=["POST"])
def train_model():
    try:
        from model_train import train_and_save_model
        train_and_save_model()
        invalidate_recognizer()
        return jsonify({"ok": True, "message": "Model trained successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------- Recognize ----------
@app.route("/api/recognize", methods=["POST"])
def recognize_face():
    data = request.json or {}
    image_b64 = data.get("image")
    lat = data.get("latitude")
    lon = data.get("longitude")
    if not image_b64:
        return jsonify({"error": "image required"}), 400
    recognizer, id_to_name = get_recognizer()
    if recognizer is None:
        return jsonify({"error": "Model not trained yet"}), 503
    try:
        img = cv2.imdecode(
            np.frombuffer(base64.b64decode(image_b64.split(",")[-1] if "," in image_b64 else image_b64), np.uint8),
            cv2.IMREAD_GRAYSCALE,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    if img is None:
        return jsonify({"error": "Invalid image"}), 400
    cascade = get_face_detector()
    faces = cascade.detectMultiScale(img, scaleFactor=1.2, minNeighbors=5, minSize=(80, 80))
    if len(faces) == 0:
        return jsonify({"recognized": False, "message": "No face detected"})
    x, y, w, h = faces[0]
    face_roi = cv2.resize(img[y:y+h, x:x+w], (200, 200))
    label_id, conf = recognizer.predict(face_roi)
    acc_pct = max(0, 100 - conf)
    if label_id not in id_to_name or conf > CONFIDENCE_THRESHOLD:
        return jsonify({"recognized": False, "confidence": acc_pct})
    user_name = id_to_name[label_id]
    location_ok = True
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT latitude, longitude FROM user_locations WHERE user_id = %s ORDER BY registered_at DESC LIMIT 1",
                (label_id,),
            )
            loc = cur.fetchone()
            if loc and lat is not None and lon is not None:
                location_ok = is_near_registered_location(lat, lon, loc["latitude"], loc["longitude"], LOCATION_ACCURACY_THRESHOLD)
            elif not loc and lat is not None and lon is not None:
                cur.execute(
                    "INSERT INTO user_locations (user_id, latitude, longitude, registered_at) VALUES (%s, %s, %s, %s)",
                    (label_id, lat, lon, datetime.utcnow().isoformat()),
                )
            cur.execute(
                "SELECT center_lat, center_lon, radius_meters FROM campus_boundaries WHERE is_active = 1 LIMIT 1"
            )
            campus = cur.fetchone()
    if campus and lat is not None and lon is not None:
        location_ok = location_ok and is_within_campus(lat, lon, campus["center_lat"], campus["center_lon"], campus["radius_meters"])
    return jsonify({
        "recognized": True,
        "user_id": label_id,
        "name": user_name,
        "confidence": acc_pct,
        "location_ok": location_ok,
    })


# ---------- Mark attendance ----------
@app.route("/api/attendance/mark", methods=["POST"])
def mark_attendance():
    data = request.json or {}
    user_id = data.get("user_id")
    user_name = data.get("user_name")
    attendance_type = data.get("type", "in")
    lat = data.get("latitude")
    lon = data.get("longitude")
    on_campus = 1 if data.get("location_ok", True) else 0
    if not user_id or not user_name:
        return jsonify({"error": "user_id and user_name required"}), 400
    now = datetime.utcnow()
    today = now.date().isoformat()
    ts = now.time().strftime("%H:%M:%S")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, in_time, out_time FROM attendance WHERE user_id = %s AND date = %s",
                (user_id, today),
            )
            row = cur.fetchone()
            if row:
                rec_id, in_time, out_time = row["id"], row["in_time"], row["out_time"]
                if attendance_type == "in":
                    if in_time:
                        return jsonify({"message": f"Already marked IN at {in_time}"})
                    cur.execute(
                        "UPDATE attendance SET in_time = %s, status = 'partial', latitude = %s, longitude = %s, on_campus = %s WHERE id = %s",
                        (ts, lat, lon, on_campus, rec_id),
                    )
                else:
                    if out_time:
                        return jsonify({"message": f"Already marked OUT at {out_time}"})
                    if not in_time:
                        return jsonify({"error": "Must mark IN first"}), 400
                    cur.execute("UPDATE attendance SET out_time = %s, status = 'present' WHERE id = %s", (ts, rec_id))
            else:
                if attendance_type == "in":
                    cur.execute(
                        """INSERT INTO attendance (user_id, date, in_time, status, latitude, longitude, on_campus, created_at)
                           VALUES (%s, %s, %s, 'partial', %s, %s, %s, %s)""",
                        (user_id, today, ts, lat, lon, on_campus, now.isoformat()),
                    )
                else:
                    return jsonify({"error": "Must mark IN first"}), 400
    return jsonify({"message": f"{user_name} marked {attendance_type.upper()} at {ts}"})


# ---------- Attendance list ----------
@app.route("/api/attendance", methods=["GET"])
def list_attendance():
    d = request.args.get("date", date.today().isoformat())
    role = request.args.get("role")
    user_id = request.args.get("user_id", type=int)
    with get_connection() as conn:
        with conn.cursor() as cur:
            if role == "class_teacher" and user_id:
                cur.execute("""
                    SELECT a.*, s.first_name, s.last_name, s.email FROM attendance a
                    JOIN students s ON s.user_id = a.user_id
                    WHERE s.class_teacher_id = %s AND a.date = %s
                    ORDER BY s.first_name, s.last_name
                """, (user_id, d))
            else:
                cur.execute("""
                    SELECT a.*,
                        COALESCE(CONCAT(s.first_name, ' ', s.last_name), CONCAT(st.first_name, ' ', st.last_name)) as name,
                        COALESCE(s.email, st.email) as email
                    FROM attendance a
                    LEFT JOIN students s ON s.user_id = a.user_id
                    LEFT JOIN staff st ON st.user_id = a.user_id
                    WHERE a.date = %s
                    ORDER BY name
                """, (d,))
            rows = cur.fetchall()
    return jsonify({"attendance": rows})


# ---------- Attendance stats (day/week/month/custom) ----------
@app.route("/api/attendance/stats", methods=["GET"])
def attendance_stats():
    role = request.args.get("role")
    user_id = request.args.get("user_id", type=int)
    start = request.args.get("start", date.today().isoformat())
    end = request.args.get("end", date.today().isoformat())
    with get_connection() as conn:
        with conn.cursor() as cur:
            if role == "class_teacher" and user_id:
                cur.execute("""
                    SELECT a.date, a.status, COUNT(*) as cnt FROM attendance a
                    JOIN students s ON s.user_id = a.user_id
                    WHERE s.class_teacher_id = %s AND a.date BETWEEN %s AND %s
                    GROUP BY a.date, a.status
                """, (user_id, start, end))
            else:
                cur.execute("""
                    SELECT date, status, COUNT(*) as cnt FROM attendance
                    WHERE date BETWEEN %s AND %s
                    GROUP BY date, status
                """, (start, end))
            rows = cur.fetchall()
    by_date = {}
    for r in rows:
        d, status, cnt = r
        if d not in by_date:
            by_date[d] = {"present": 0, "partial": 0, "absent": 0}
        by_date[d][status] = cnt
    return jsonify({"stats": by_date, "start": start, "end": end})


# ---------- Export Excel (day/week/month/custom) ----------
@app.route("/api/export", methods=["GET"])
def export_attendance():
    role = request.args.get("role", "admin")
    user_id = request.args.get("user_id", type=int, default=1)
    start = request.args.get("start", date.today().isoformat())
    end = request.args.get("end", date.today().isoformat())
    export_type = request.args.get("export_type", "students")  # students | staff
    try:
        path = export_to_excel(role, user_id, start, end, export_type)
        return send_file(path, as_attachment=True, download_name=os.path.basename(path))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------- Campus ----------
@app.route("/api/campus", methods=["GET"])
def get_campus():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM campus_boundaries WHERE is_active = 1 LIMIT 1")
            row = cur.fetchone()
    return jsonify({"campus": row})


@app.route("/api/campus", methods=["POST"])
def set_campus():
    data = request.json or {}
    lat = data.get("latitude")
    lon = data.get("longitude")
    radius = data.get("radius_meters", 500)
    name = data.get("name", "Main Campus")
    if lat is None or lon is None:
        return jsonify({"error": "latitude and longitude required"}), 400
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE campus_boundaries SET is_active = 0")
            cur.execute(
                "INSERT INTO campus_boundaries (name, center_lat, center_lon, radius_meters) VALUES (%s, %s, %s, %s)",
                (name, lat, lon, radius),
            )
    return jsonify({"ok": True})


# ---------- Face registry (admin: all with face + location) ----------
@app.route("/api/face-registry", methods=["GET"])
def face_registry():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT fr.user_id, fr.face_encoding_path, fr.samples_count, fr.registered_at,
                    COALESCE(CONCAT(s.first_name, ' ', s.last_name), CONCAT(st.first_name, ' ', st.last_name)) as name,
                    COALESCE(s.email, st.email) as email,
                    CASE WHEN s.user_id IS NOT NULL THEN 'student' ELSE 'staff' END as role
                FROM face_registry fr
                LEFT JOIN students s ON s.user_id = fr.user_id
                LEFT JOIN staff st ON st.user_id = fr.user_id
                ORDER BY name
            """)
            registry = cur.fetchall()
        with conn.cursor() as cur:
            for r in registry:
                cur.execute(
                    "SELECT latitude, longitude, registered_at FROM user_locations WHERE user_id = %s ORDER BY registered_at DESC LIMIT 1",
                    (r["user_id"],),
                )
                loc = cur.fetchone()
                r["latitude"] = loc["latitude"] if loc else None
                r["longitude"] = loc["longitude"] if loc else None
                r["location_registered"] = loc["registered_at"] if loc else None
    return jsonify({"registry": registry})


# ---------- Single student record (for class teacher / admin) ----------
@app.route("/api/students/<int:user_id>/record", methods=["GET"])
def get_student_record(user_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT s.*, d.name as department_name, deg.name as degree_name
                FROM students s
                LEFT JOIN departments d ON d.id = s.department_id
                LEFT JOIN degrees deg ON deg.id = s.degree_id
                WHERE s.user_id = %s
            """, (user_id,))
            row = cur.fetchone()
            if not row:
                return jsonify({"error": "Not found"}), 404
            rec = dict(row)
            cur.execute(
                "SELECT latitude, longitude, registered_at FROM user_locations WHERE user_id = %s ORDER BY registered_at DESC LIMIT 1",
                (user_id,),
            )
            loc = cur.fetchone()
            rec["latitude"] = loc["latitude"] if loc else None
            rec["longitude"] = loc["longitude"] if loc else None
            rec["location_registered"] = loc["registered_at"] if loc else None
            cur.execute("SELECT samples_count, registered_at FROM face_registry WHERE user_id = %s", (user_id,))
            fr = cur.fetchone()
            rec["face_samples"] = fr["samples_count"] if fr else 0
            rec["face_registered_at"] = fr["registered_at"] if fr else None
    return jsonify(rec)


# ---------- Single staff record ----------
@app.route("/api/staff/<int:user_id>/record", methods=["GET"])
def get_staff_record(user_id):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT s.*, d.name as department_name FROM staff s
                LEFT JOIN departments d ON d.id = s.department_id
                WHERE s.user_id = %s
            """, (user_id,))
            row = cur.fetchone()
            if not row:
                return jsonify({"error": "Not found"}), 404
            rec = dict(row)
            cur.execute(
                "SELECT latitude, longitude, registered_at FROM user_locations WHERE user_id = %s ORDER BY registered_at DESC LIMIT 1",
                (user_id,),
            )
            loc = cur.fetchone()
            rec["latitude"] = loc["latitude"] if loc else None
            rec["longitude"] = loc["longitude"] if loc else None
            rec["location_registered"] = loc["registered_at"] if loc else None
            cur.execute("SELECT samples_count, registered_at FROM face_registry WHERE user_id = %s", (user_id,))
            fr = cur.fetchone()
            rec["face_samples"] = fr["samples_count"] if fr else 0
            rec["face_registered_at"] = fr["registered_at"] if fr else None
    return jsonify(rec)


@app.route("/uploads/<path:filename>")
def serve_upload(filename):
    return send_from_directory(UPLOADS_DIR, filename)


def ensure_db():
    from database.init_db import init_database
    init_database()


if __name__ == "__main__":
    os.makedirs(DATASET_DIR, exist_ok=True)
    os.makedirs(MODELS_DIR, exist_ok=True)
    os.makedirs(EXPORTS_DIR, exist_ok=True)
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM users LIMIT 1")
    except Exception:
        ensure_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
