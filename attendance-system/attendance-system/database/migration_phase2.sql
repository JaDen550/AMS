-- ============================================================
-- Phase 2 Migration: Courses, Lecturer Sessions, Module-Linked Attendance
-- Run this AFTER the Phase 1 schema is already in place.
-- Run this directly in Railway's MySQL Console (same way as schema.sql).
-- ============================================================

USE railway;

CREATE TABLE courses (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    module_code     VARCHAR(20) NOT NULL UNIQUE,
    module_name     VARCHAR(150) NOT NULL,
    lecturer_id     INT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (lecturer_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE attendance_sessions (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    course_id       INT NOT NULL,
    device_id       INT NOT NULL,
    lecturer_id     INT NOT NULL,
    started_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at        TIMESTAMP NULL,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE,
    FOREIGN KEY (lecturer_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_device_active (device_id, is_active)
);

ALTER TABLE attendance_records
    ADD COLUMN session_id INT NULL AFTER device_id,
    ADD FOREIGN KEY (session_id) REFERENCES attendance_sessions(id) ON DELETE SET NULL;
