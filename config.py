"""FaceSense configuration."""
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Paths
DATASET_DIR = os.path.join(BASE_DIR, "dataset")
MODELS_DIR = os.path.join(BASE_DIR, "models")
EXPORTS_DIR = os.path.join(BASE_DIR, "exports")
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
FRONTEND_BUILD_DIR = os.path.join(BASE_DIR, "frontend", "dist")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "pdf"}

MODEL_PATH = os.path.join(MODELS_DIR, "face_lbph.xml")
LABELS_PATH = os.path.join(MODELS_DIR, "labels.json")

# MySQL connection (main database - all collected and stored data lives here)
MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", "3306"))
MYSQL_USER = os.environ.get("MYSQL_USER", "root")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "Dharaan007")
MYSQL_DATABASE = os.environ.get("MYSQL_DATABASE", "facesense")

# Face recognition settings
CONFIDENCE_THRESHOLD = 20.0  # LBPH: lower is better. ~20 = 80% accuracy
SAMPLES_PER_PERSON = 30
FACE_IMAGE_SIZE = (200, 200)

# Location / campus verification
CAMPUS_RADIUS_METERS = 500  # Default radius for campus boundary
LOCATION_ACCURACY_THRESHOLD = 100  # Max meters variance allowed
