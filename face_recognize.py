"""
FaceSense - Recognition with pattern overlay, 80% accuracy check, and location verification.
Uses MySQL for location and attendance.
"""
import os
import json
from datetime import datetime, date
from typing import Tuple, Dict, Optional

import cv2
import numpy as np

from config import (
    MODELS_DIR, MODEL_PATH, LABELS_PATH, EXPORTS_DIR,
    CONFIDENCE_THRESHOLD, LOCATION_ACCURACY_THRESHOLD
)
from db import get_connection
from utils.pattern_formation import draw_pattern_formation_ui
from utils.location_utils import is_near_registered_location, is_within_campus


def ensure_setup():
    os.makedirs(MODELS_DIR, exist_ok=True)
    os.makedirs(EXPORTS_DIR, exist_ok=True)


def load_model_and_labels() -> Tuple:
    if not os.path.isfile(MODEL_PATH) or not os.path.isfile(LABELS_PATH):
        raise RuntimeError("Model not found. Train first by running model_train.py")

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(MODEL_PATH)
    with open(LABELS_PATH, "r", encoding="utf-8") as f:
        meta = json.load(f)
        id_to_name = {int(k): v for k, v in meta.get("id_to_name", {}).items()}

    return recognizer, id_to_name


def get_face_detector():
    cascade_path = os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
    face_cascade = cv2.CascadeClassifier(cascade_path)
    if face_cascade.empty():
        raise RuntimeError("Failed to load Haar cascade.")
    return face_cascade


def get_user_registered_location(user_id: int) -> Optional[Tuple[float, float]]:
    """Get the location where user first registered (for anti-fraud check)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT latitude, longitude FROM user_locations WHERE user_id = %s ORDER BY registered_at DESC LIMIT 1",
                (user_id,),
            )
            row = cur.fetchone()
    return (row["latitude"], row["longitude"]) if row else None


def get_campus_boundary() -> Optional[Tuple[float, float, float]]:
    """Get active campus center and radius (lat, lon, radius_m)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT center_lat, center_lon, radius_meters FROM campus_boundaries WHERE is_active = 1 LIMIT 1"
            )
            row = cur.fetchone()
    return (row["center_lat"], row["center_lon"], row["radius_meters"]) if row else None


def save_user_location(user_id: int, lat: float, lon: float, accuracy: Optional[float] = None):
    """Store location on first registration."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO user_locations (user_id, latitude, longitude, accuracy, registered_at) VALUES (%s, %s, %s, %s, %s)",
                (user_id, lat, lon, accuracy, datetime.utcnow().isoformat()),
            )


def log_attendance(user_id: int, user_name: str, attendance_type: str, lat: Optional[float] = None,
                   lon: Optional[float] = None, on_campus: int = 1) -> str:
    """Log attendance with location data."""
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
                        return f"{user_name} already marked IN at {in_time}"
                    cur.execute(
                        "UPDATE attendance SET in_time = %s, status = 'partial', latitude = %s, longitude = %s, on_campus = %s WHERE id = %s",
                        (ts, lat, lon, on_campus, rec_id),
                    )
                else:
                    if out_time:
                        return f"{user_name} already marked OUT at {out_time}"
                    if not in_time:
                        return f"{user_name} must mark IN first"
                    cur.execute(
                        "UPDATE attendance SET out_time = %s, status = 'present' WHERE id = %s",
                        (ts, rec_id),
                    )
            else:
                if attendance_type == "in":
                    cur.execute(
                        """INSERT INTO attendance (user_id, date, in_time, status, latitude, longitude, on_campus, created_at)
                           VALUES (%s, %s, %s, 'partial', %s, %s, %s, %s)""",
                        (user_id, today, ts, lat, lon, on_campus, now.isoformat()),
                    )
                else:
                    return f"{user_name} must mark IN first"

    return f"{user_name} marked {attendance_type.upper()} at {ts}"


def recognize_loop(confidence_threshold: float = CONFIDENCE_THRESHOLD,
                  lat: Optional[float] = None, lon: Optional[float] = None,
                  on_mark_callback=None):
    """
    Main recognition loop with pattern overlay and location verification.
    """
    recognizer, id_to_name = load_model_and_labels()
    face_cascade = get_face_detector()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Webcam not accessible.")

    last_attendance = {}
    cooldown_sec = 5
    frame_count = 0

    print("[INFO] FaceSense Recognition - Press 'i' IN, 'o' OUT, 'e' export, 'q' quit")

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        frame_count += 1
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(80, 80))

        recognized_user_id = None
        recognized_name = None
        match_confidence = 0
        location_ok = True

        for (x, y, w, h) in faces:
            face_roi = cv2.resize(gray[y:y+h, x:x+w], (200, 200))
            label_id, conf = recognizer.predict(face_roi)
            acc_pct = max(0, 100 - conf)

            if label_id in id_to_name and conf < confidence_threshold:
                recognized_user_id = label_id
                recognized_name = id_to_name[label_id]
                match_confidence = acc_pct

                reg_loc = get_user_registered_location(label_id)
                if reg_loc and lat is not None and lon is not None:
                    location_ok = is_near_registered_location(lat, lon, reg_loc[0], reg_loc[1], LOCATION_ACCURACY_THRESHOLD)
                elif not reg_loc and lat is not None and lon is not None:
                    save_user_location(label_id, lat, lon)

                campus = get_campus_boundary()
                if campus and lat is not None and lon is not None:
                    location_ok = location_ok and is_within_campus(lat, lon, campus[0], campus[1], campus[2])

            status = f"{recognized_name} ({acc_pct:.0f}%)" if recognized_name else "Unknown"
            if not location_ok:
                status += " | Location mismatch!"
            frame = draw_pattern_formation_ui(frame, [(x, y, w, h)], status, frame_count * 0.05)

            color = (0, 255, 0) if (recognized_name and location_ok) else (0, 0, 255)
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)

        cv2.imshow("FaceSense Recognition", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            break
        elif key == ord('i') or key == ord('o'):
            if recognized_user_id and recognized_name and location_ok and len(faces) > 0:
                now = datetime.utcnow()
                if recognized_user_id in last_attendance:
                    if (now - last_attendance[recognized_user_id]).seconds < cooldown_sec:
                        continue
                att_type = "in" if key == ord('i') else "out"
                msg = log_attendance(recognized_user_id, recognized_name, att_type, lat, lon, 1 if location_ok else 0)
                print(f"[INFO] {msg}")
                last_attendance[recognized_user_id] = now
                if on_mark_callback:
                    on_mark_callback(msg)
            elif recognized_user_id and not location_ok:
                print("[WARN] Location verification failed - attendance not recorded.")

    cap.release()
    cv2.destroyAllWindows()
