"""Initialize FaceSense MySQL database: create database if needed, then run schema."""
import os
import sys
from pathlib import Path
import pymysql

# Ensure project root (where config.py lives) is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")


def init_database():
    """Create database (if not exists) and apply schema."""
    # Connect without database to create it
    conn = pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        charset="utf8mb4",
    )
    try:
        with conn.cursor() as cur:
            cur.execute(f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DATABASE}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        conn.commit()
    finally:
        conn.close()

    conn = pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
        charset="utf8mb4",
    )
    try:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            schema = f.read()
        # Split by semicolon and run each non-empty statement
        parts = schema.split(";")
        with conn.cursor() as cur:
            for part in parts:
                stmt = part.strip()
                # Skip comments-only and empty
                lines = [l.strip() for l in stmt.split("\n") if l.strip() and not l.strip().startswith("--")]
                stmt = " ".join(lines)
                if not stmt:
                    continue
                try:
                    cur.execute(stmt + ";")
                except pymysql.err.OperationalError as e:
                    # 1061 duplicate key name, 1050 table exists, 1062 duplicate entry
                    if e.args[0] in (1061, 1050, 1062):
                        pass
                    else:
                        raise
        conn.commit()
        print(f"[INFO] MySQL database '{MYSQL_DATABASE}' initialized at {MYSQL_HOST}:{MYSQL_PORT}")
    finally:
        conn.close()


if __name__ == "__main__":
    init_database()
