"""
FaceSense - Model training from stored face data. Uses MySQL.
"""
import os
import json
import cv2
import numpy as np
from datetime import datetime

from config import DATASET_DIR, MODELS_DIR, MODEL_PATH, LABELS_PATH, FACE_IMAGE_SIZE
from db import get_connection


def ensure_directories():
    os.makedirs(DATASET_DIR, exist_ok=True)
    os.makedirs(MODELS_DIR, exist_ok=True)


def build_training_data_from_db():
    """Build training data from dataset folder, mapped by user_id from MySQL."""
    images = []
    labels = []
    id_to_name = {}

    if not os.path.isdir(DATASET_DIR):
        raise RuntimeError(f"Dataset directory not found at {DATASET_DIR}. Capture data first.")

    for user_dir_name in sorted(os.listdir(DATASET_DIR)):
        user_dir = os.path.join(DATASET_DIR, user_dir_name)
        if not os.path.isdir(user_dir):
            continue

        try:
            user_id = int(user_dir_name)
        except ValueError:
            continue

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT first_name, last_name FROM students WHERE user_id = %s",
                    (user_id,),
                )
                row = cur.fetchone()
                if not row:
                    cur.execute(
                        "SELECT first_name, last_name FROM staff WHERE user_id = %s",
                        (user_id,),
                    )
                    row = cur.fetchone()
                if not row:
                    continue
                user_name = f"{row.get('first_name') or ''} {row.get('last_name') or ''}".strip() or str(user_id)

        id_to_name[user_id] = user_name

        for file in sorted(os.listdir(user_dir)):
            if not file.lower().endswith((".png", ".jpg", ".jpeg")):
                continue
            img_path = os.path.join(user_dir, file)
            img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                continue
            img = cv2.resize(img, FACE_IMAGE_SIZE)
            images.append(img)
            labels.append(user_id)

    if not images:
        raise RuntimeError("No training images found. Please capture data first.")

    name_to_id = {v: k for k, v in id_to_name.items()}
    return images, np.array(labels, dtype=np.int32), name_to_id, id_to_name


def train_and_save_model():
    """Train LBPH recognizer and save model + labels."""
    ensure_directories()
    print("[INFO] Preparing training data from database...")
    images, labels, name_to_id, id_to_name = build_training_data_from_db()

    try:
        recognizer = cv2.face.LBPHFaceRecognizer_create(radius=1, neighbors=8, grid_x=8, grid_y=8)
    except AttributeError:
        raise RuntimeError("Install opencv-contrib-python: pip install opencv-contrib-python")

    print("[INFO] Training LBPH face recognizer (80% accuracy target)...")
    recognizer.train(images, labels)

    recognizer.save(MODEL_PATH)
    meta = {
        "name_to_id": {k: int(v) for k, v in name_to_id.items()},
        "id_to_name": {int(k): v for k, v in id_to_name.items()},
        "trained_at": datetime.utcnow().isoformat(),
    }
    with open(LABELS_PATH, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(f"[INFO] Model saved: {MODEL_PATH}")
    print(f"[INFO] Labels saved: {LABELS_PATH}")
    return True
