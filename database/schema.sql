-- FaceSense Database Schema - MySQL
-- Run this once after creating the database to create tables and insert default admin.

-- Departments
CREATE TABLE IF NOT EXISTS departments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Degrees (courses)
CREATE TABLE IF NOT EXISTS degrees (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Base users (login: admin, student, staff)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    role ENUM('admin', 'staff', 'student') NOT NULL,
    is_active TINYINT(1) DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Students (extended profile)
CREATE TABLE IF NOT EXISTS students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    father_name VARCHAR(255),
    mother_name VARCHAR(255),
    phone VARCHAR(50),
    email VARCHAR(255),
    parents_number VARCHAR(50),
    id_card_path VARCHAR(500),
    hair_colour VARCHAR(50),
    eye_colour VARCHAR(50),
    blood_group VARCHAR(20),
    year_of_study INT,
    semester INT,
    department_id INT,
    degree_id INT,
    hod_name VARCHAR(255),
    class_teacher_id INT,
    shift_type ENUM('full_time', 'part_time'),
    shift_time ENUM('morning', 'afternoon'),
    accept_rules TINYINT(1) DEFAULT 0,
    accept_face_recognition TINYINT(1) DEFAULT 0,
    location_permission TINYINT(1) DEFAULT 0,
    semester_face_updated_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL,
    FOREIGN KEY (degree_id) REFERENCES degrees(id) ON DELETE SET NULL,
    FOREIGN KEY (class_teacher_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Staff (extended profile)
CREATE TABLE IF NOT EXISTS staff (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    father_name VARCHAR(255),
    mother_or_spouse_name VARCHAR(255),
    phone VARCHAR(50),
    email VARCHAR(255),
    marital_status VARCHAR(50),
    parents_or_spouse_number VARCHAR(50),
    id_card_path VARCHAR(500),
    hair_colour VARCHAR(50),
    eye_colour VARCHAR(50),
    blood_group VARCHAR(20),
    degree_completed VARCHAR(255),
    department_id INT,
    hod_name VARCHAR(255),
    accept_rules TINYINT(1) DEFAULT 0,
    accept_face_recognition TINYINT(1) DEFAULT 0,
    location_permission TINYINT(1) DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL
);

-- Face registry
CREATE TABLE IF NOT EXISTS face_registry (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    face_encoding_path VARCHAR(500) NOT NULL,
    samples_count INT DEFAULT 0,
    registered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- User locations (campus)
CREATE TABLE IF NOT EXISTS user_locations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    latitude DOUBLE NOT NULL,
    longitude DOUBLE NOT NULL,
    accuracy DOUBLE,
    registered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Campus boundary
CREATE TABLE IF NOT EXISTS campus_boundaries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    center_lat DOUBLE NOT NULL,
    center_lon DOUBLE NOT NULL,
    radius_meters DOUBLE NOT NULL DEFAULT 500,
    is_active TINYINT(1) DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Attendance
CREATE TABLE IF NOT EXISTS attendance (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    date DATE NOT NULL,
    in_time TIME,
    out_time TIME,
    status ENUM('present', 'partial', 'absent') NOT NULL DEFAULT 'partial',
    latitude DOUBLE,
    longitude DOUBLE,
    on_campus TINYINT(1) DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY uk_user_date (user_id, date)
);

-- Indexes
CREATE INDEX idx_attendance_user_date ON attendance(user_id, date);
CREATE INDEX idx_attendance_date ON attendance(date);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_students_class_teacher ON students(class_teacher_id);
CREATE INDEX idx_students_degree_dept ON students(degree_id, department_id, year_of_study, semester);
CREATE INDEX idx_staff_department ON staff(department_id);

-- Default admin user
INSERT INTO users (id, email, password_hash, role)
VALUES (1, 'admin@facesense.com', 'admin123', 'admin')
ON DUPLICATE KEY UPDATE email = VALUES(email);
