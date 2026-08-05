-- ============================================================
-- Solar-Powered Biometric Attendance Management System
-- Database Schema — Phase 1 (Core Loop)
-- Engine: MySQL 8
--
-- Phase 2+ tables (departments, faculties, courses, sessions,
-- notifications, audit_logs, battery_logs, system_settings) are
-- deliberately NOT in this file yet. They'll be added as
-- migrations once Phase 1 is working end to end, so we don't
-- carry unused tables while the core loop is still being proven.
-- ============================================================

CREATE DATABASE IF NOT EXISTS attendance_system
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE attendance_system;

-- ------------------------------------------------------------
-- users: login accounts. Phase 1 = admin only in practice,
-- but the role column exists from day one so Phase 2 (lecturer/
-- student login) doesn't require a schema migration.
-- ------------------------------------------------------------
CREATE TABLE users (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    email           VARCHAR(120) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,      -- bcrypt hash
    role            ENUM('admin', 'lecturer', 'student') NOT NULL DEFAULT 'admin',
    full_name       VARCHAR(150) NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- students: the enrolled population. Linked 1:1 to a users row
-- once Phase 2 gives students login access — nullable for now.
-- ------------------------------------------------------------
CREATE TABLE students (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    user_id         INT NULL,
    student_number  VARCHAR(30) NOT NULL UNIQUE,
    full_name       VARCHAR(150) NOT NULL,
    email           VARCHAR(120),
    phone           VARCHAR(30),
    fingerprint_id  INT NULL UNIQUE,             -- ID slot on the AS608/R307 sensor
    is_enrolled     BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- ------------------------------------------------------------
-- devices: each physical ESP32 unit. Even in Phase 1 with one
-- device, modeling this properly now avoids a painful migration
-- when Phase 4 adds multi-device support.
-- ------------------------------------------------------------
CREATE TABLE devices (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    device_uid      VARCHAR(64) NOT NULL UNIQUE,  -- e.g. ESP32 MAC address
    label           VARCHAR(100) NOT NULL,        -- e.g. "Main Gate Reader"
    location        VARCHAR(150),
    api_key         VARCHAR(255) NOT NULL,        -- device auth to the API
    last_seen_at    TIMESTAMP NULL,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ------------------------------------------------------------
-- attendance_records: the core transactional table.
-- ------------------------------------------------------------
CREATE TABLE attendance_records (
    id                  BIGINT AUTO_INCREMENT PRIMARY KEY,
    student_id          INT NOT NULL,
    device_id           INT NOT NULL,
    fingerprint_id      INT NOT NULL,             -- matched sensor slot, for traceability
    status              ENUM('present', 'late') NOT NULL DEFAULT 'present',
    recorded_at         DATETIME NOT NULL,        -- timestamp from device (device clock)
    received_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- when server actually got it
    synced_offline       BOOLEAN NOT NULL DEFAULT FALSE, -- TRUE if this came from the offline queue
    battery_percentage  TINYINT NULL,
    network_status      ENUM('online', 'offline_queued') NOT NULL DEFAULT 'online',
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
    FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE RESTRICT,
    INDEX idx_student_date (student_id, recorded_at),
    INDEX idx_device_date (device_id, recorded_at)
);

-- ------------------------------------------------------------
-- Seed: one admin user for first login.
-- Password below is a PLACEHOLDER hash — replace via the
-- backend's user-creation script, never hardcode a real
-- password hash in version control.
-- ------------------------------------------------------------
INSERT INTO users (email, password_hash, role, full_name)
VALUES ('admin@example.com', 'REPLACE_WITH_BCRYPT_HASH', 'admin', 'System Administrator');
