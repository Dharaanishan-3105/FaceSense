"""
FaceSense - Excel export with role-based access. Uses MySQL.
"""
import os
from datetime import date
from typing import Optional

import pandas as pd

from config import EXPORTS_DIR
from db import get_connection_raw


def get_students_attendance_for_export(
    class_teacher_user_id: int, start_date: str, end_date: str
) -> pd.DataFrame:
    """Class teacher: students where class_teacher_id = class_teacher_user_id."""
    conn = get_connection_raw()
    try:
        query = """
            SELECT a.user_id, a.date, a.in_time, a.out_time, a.status, a.on_campus,
                   s.first_name, s.last_name, s.email, s.phone, s.degree_id, s.department_id, s.year_of_study, s.semester
            FROM attendance a
            JOIN students s ON s.user_id = a.user_id
            WHERE s.class_teacher_id = %s AND a.date BETWEEN %s AND %s
            ORDER BY a.date DESC, s.first_name, s.last_name
        """
        df = pd.read_sql_query(query, conn, params=(class_teacher_user_id, start_date, end_date))
        if not df.empty:
            df["name"] = df["first_name"].fillna("") + " " + df["last_name"].fillna("")
        return df
    finally:
        conn.close()


def get_all_students_attendance_for_export(start_date: str, end_date: str) -> pd.DataFrame:
    """Admin: all students' attendance."""
    conn = get_connection_raw()
    try:
        query = """
            SELECT a.user_id, a.date, a.in_time, a.out_time, a.status, a.on_campus,
                   s.first_name, s.last_name, s.email, s.phone
            FROM attendance a
            JOIN students s ON s.user_id = a.user_id
            WHERE a.date BETWEEN %s AND %s
            ORDER BY a.date DESC, s.first_name, s.last_name
        """
        df = pd.read_sql_query(query, conn, params=(start_date, end_date))
        if not df.empty:
            df["name"] = df["first_name"].fillna("") + " " + df["last_name"].fillna("")
        return df
    finally:
        conn.close()


def get_staff_attendance_for_export(start_date: str, end_date: str) -> pd.DataFrame:
    """Admin: all staff attendance."""
    conn = get_connection_raw()
    try:
        query = """
            SELECT a.user_id, a.date, a.in_time, a.out_time, a.status, a.on_campus,
                   s.first_name, s.last_name, s.email, s.phone, s.department_id
            FROM attendance a
            JOIN staff s ON s.user_id = a.user_id
            WHERE a.date BETWEEN %s AND %s
            ORDER BY a.date DESC, s.first_name, s.last_name
        """
        df = pd.read_sql_query(query, conn, params=(start_date, end_date))
        if not df.empty:
            df["name"] = df["first_name"].fillna("") + " " + df["last_name"].fillna("")
        return df
    finally:
        conn.close()


def export_to_excel(
    role: str,
    user_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    export_type: str = "students",
) -> str:
    """Returns file path."""
    os.makedirs(EXPORTS_DIR, exist_ok=True)
    if not start_date:
        start_date = date.today().isoformat()
    if not end_date:
        end_date = start_date

    if role == "class_teacher":
        df = get_students_attendance_for_export(user_id, start_date, end_date)
    elif role == "admin" and export_type == "staff":
        df = get_staff_attendance_for_export(start_date, end_date)
    else:
        df = get_all_students_attendance_for_export(start_date, end_date)

    filename = f"attendance_{start_date}_to_{end_date}.xlsx"
    filepath = os.path.join(EXPORTS_DIR, filename)

    if df.empty:
        summary = pd.DataFrame({"Info": ["No attendance records for the selected period."]})
        with pd.ExcelWriter(filepath, engine="openpyxl") as w:
            summary.to_excel(w, sheet_name="Summary", index=False)
    else:
        present = len(df[df["status"] == "present"])
        partial = len(df[df["status"] == "partial"])
        total_records = len(df)
        summary = pd.DataFrame({
            "Metric": ["Total Records", "Full Attendance (IN+OUT)", "Partial (IN only)", "Unique Days"],
            "Value": [total_records, present, partial, df["date"].nunique()],
        })
        with pd.ExcelWriter(filepath, engine="openpyxl") as w:
            df.to_excel(w, sheet_name="Attendance", index=False)
            summary.to_excel(w, sheet_name="Summary", index=False)
    return filepath
