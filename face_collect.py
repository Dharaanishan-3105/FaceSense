"""
FaceSense - Real-time face data collection with unique pattern formation overlay.
Collects face samples, stores in dataset, captures location on first registration.
"""
import os
import cv2
import numpy as np
from datetime import datetime
from typing import Optional

from config import (
    DATASET_DIR, MODELS_DIR, SAMPLES_PER_PERSON, FACE_IMAGE_SIZE,
)
from db import get_connection
from utils.pattern_formation import draw_pattern_formation_ui


def ensure_directories():
    os.makedirs(DATASET_DIR, exist_ok=True)
    os.makedirs(MODELS_DIR, exist_ok=True)


def get_face_detector():
    cascade_path = os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
    face_cascade = cv2.CascadeClassifier(cascade_path)
    if face_cascade.empty():
        raise RuntimeError("Failed to load Haar cascade for face detection.")
    return face_cascade


def capture_faces_for_user(user_id: int, user_name: str, samples: int = SAMPLES_PER_PERSON,
                           camera_index: int = 0) -> int:
    """
    Capture face samples with real-time pattern formation overlay.
    Returns number of samples captured.
    """
    user_dir = os.path.join(DATASET_DIR, str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    
    face_cascade = get_face_detector()
    cap = cv2.VideoCapture(camera_index)
    
    if not cap.isOpened():
        raise RuntimeError("Webcam not accessible. Ensure a camera is connected.")
    
    captured = 0
    frame_count = 0
    
    try:
        while captured < samples:
            ret, frame = cap.read()
            if not ret:
                continue
            
            frame_count += 1
            animate_phase = frame_count * 0.05
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(80, 80))
            
            status = f"Captured {captured}/{samples} - Align face in frame"
            frame = draw_pattern_formation_ui(frame, faces, status, animate_phase)
            
            for (x, y, w, h) in faces:
                face_roi = gray[y:y + h, x:x + w]
                face_resized = cv2.resize(face_roi, FACE_IMAGE_SIZE)
                img_path = os.path.join(user_dir, f"{user_name}_{captured + 1:03d}.jpg")
                cv2.imwrite(img_path, face_resized)
                captured += 1
                
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, f"{user_name} {captured}/{samples}", (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
                if captured >= samples:
                    break
            
            cv2.imshow("FaceSense - Capture (Pattern Formation)", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    
    finally:
        cap.release()
        cv2.destroyAllWindows()
    
    return captured


def register_face_in_db(user_id: int, samples_count: int):
    """Update face_registry after capturing."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO face_registry (user_id, face_encoding_path, samples_count, registered_at)
                   VALUES (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE face_encoding_path = VALUES(face_encoding_path),
                   samples_count = VALUES(samples_count), registered_at = VALUES(registered_at)""",
                (user_id, f"dataset/{user_id}", samples_count, datetime.utcnow().isoformat()),
            )
