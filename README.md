## FaceSense – Intelligent Face Recognition Attendance System

Modern attendance system for **students** and **staff** with face recognition, campus-location verification, and role‑based Excel exports.  
Backend and data are fully on **Python (Flask) + MySQL**, with a **React** single‑page app served by Flask in production.

---

### Key Features

- **Rich student registration**
  - First/last name, father/mother name, phone, email, parents number.
  - College ID upload, hair/eye colour, blood group.
  - Year, semester, department, degree, HOD, class teacher, shift type/time.
  - Must accept college rules, face recognition, and location (campus); face can be re‑registered each semester.
- **Detailed staff registration**
  - First/last name, father or spouse name, phone, email, marital status.
  - Parents/spouse number, college ID upload, hair/eye colour, blood group.
  - Degree completed, department, HOD.
- **Face + location attendance**
  - Face samples captured once, bound to user.
  - Campus boundary set by admin; attendance is valid only when **face matches and user is inside campus**.
- **Role‑based portals**
  - **Admin**: manage departments, degrees, staff, students; assign class teachers; train model; set campus; export attendance.
  - **Class teacher**: view assigned students, daily attendance, stats (day/week/month/custom), and export Excel.
  - **Attendance kiosk**: simple screen to recognize faces and mark IN / OUT.

---

### Tech Stack

- **Backend**: Python, Flask, OpenCV (opencv‑contrib‑python)
- **Database**: **MySQL only** via PyMySQL (all collected and stored data lives in MySQL)
- **Frontend**: React + Vite, HTML, CSS (modern gradient UI)
- **Exports / data**: pandas, openpyxl

---

### Folder Overview

```text
FaceSense/
  app.py             # Flask API (auth, students, staff, face, attendance, export)
  config.py          # Paths + MySQL settings (MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE)
  db.py              # get_connection() helper for MySQL
  database/
    schema.sql       # MySQL DDL (tables, indexes, default admin)
    init_db.py       # Creates database if needed and applies schema
  utils/
    pattern_formation.py
    location_utils.py
  export_utils.py    # Excel export for students / staff attendance
  face_collect.py
  face_recognize.py
  MYSQL_SETUP.md     # Detailed MySQL installation / connection / data viewing guide
  frontend/          # React SPA (login, admin, teacher, kiosk)
  dataset/, models/, exports/, uploads/  # Created at runtime
```

---

## Getting Started (Local Development)

### 1. MySQL

1. Install MySQL (server + client).
2. Create a user and database (see `MYSQL_SETUP.md` for exact commands).
3. Adjust `config.py` if needed:
   - `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`.

### 2. Backend (Flask)

```bash
cd FaceSense
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
python database/init_db.py  # create DB + tables + default admin
```

Then run the backend (which also serves the built React app if present):

```bash
python app.py
```

Backend will be available on `http://127.0.0.1:5000/`.

### 3. Frontend (React)

For development (hot reload):

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` while `python app.py` runs for APIs.

For production build (used when you only run `python app.py`):

```bash
cd frontend
npm run build
```

The static assets in `frontend/dist` are then served by Flask at `http://127.0.0.1:5000/`.

---

## Usage Flow

1. **Admin**
   - Log in and add departments and degrees (Admin → Students or Staff → “Add Department / Degree”).
   - Add staff either from the staff registration page or via “Quick add staff” in Admin → Staff.
2. **Staff**
   - Use “Register as Staff”, complete full profile and upload ID card.
   - Admin can trigger face registration from the Face Registry / Staff views.
3. **Students**
   - Use “Register as Student”, select department, degree, year, semester, and class teacher.
   - Admin or class teacher completes face registration.
4. **Campus & Training**
   - Admin sets campus boundary (Campus tab) and trains the face model (Registry → Train Model).
5. **Attendance**
   - Use Attendance kiosk: camera recognizes face, checks campus location, and marks IN/OUT.
6. **Exports**
   - Class teachers and admin export attendance (students / staff, custom date range) to Excel.

---
