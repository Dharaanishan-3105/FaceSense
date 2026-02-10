"""
FaceSense - MySQL database connection.
Single place for all DB access. Use get_connection() for queries; placeholder is %s.
"""
import pymysql
from pymysql.cursors import DictCursor
from contextlib import contextmanager

from config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE


@contextmanager
def get_connection():
    """Yield a MySQL connection with DictCursor. Use %s for placeholders. Commit on exit, rollback on error."""
    conn = pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
        charset="utf8mb4",
        cursorclass=DictCursor,
        autocommit=False,
    )
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_connection_raw():
    """Return a connection without context manager (e.g. for pandas). Caller must close."""
    return pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
        charset="utf8mb4",
        cursorclass=DictCursor,
    )
