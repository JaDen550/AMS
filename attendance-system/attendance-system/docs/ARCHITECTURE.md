# Solar-Powered Biometric Attendance Management System
## Architecture & Phased Roadmap

## 1. System Overview

Three tiers:

1. **Firmware tier** — ESP32 + AS608/R307 fingerprint sensor, solar-charged,
   connects over Wi-Fi to the local network. Talks to the backend via REST API.
   Queues attendance locally when offline and syncs when connectivity returns.
2. **Backend tier** — Python Flask REST API, JWT-authenticated, MySQL database
   via SQLAlchemy ORM. Owns all business logic: enrollment, attendance rules,
   reporting, RBAC.
3. **Frontend tier** — Server-rendered or API-consuming web app (Bootstrap 5 +
   JS + Chart.js) with three role-based views: Admin, Lecturer, Student.

```
[ESP32 + AS608 Sensor] --WiFi/REST--> [Flask API] <--REST/JSON--> [Web Frontend]
        |                                  |
   [Local SPIFFS queue]              [MySQL Database]
   (offline buffer)                  (source of truth)
```

Device is registered to a specific classroom/venue and is not tied to any
particular laptop — it talks to the backend server directly, wherever that
server runs (your dev laptop now, a proper host later). This is what makes
the system "install on any Windows 10+ laptop": the laptop only ever runs
the Flask server + database, never touches the fingerprint hardware directly.

## 2. Why Phased, Not All-At-Once

The original spec is a full commercial product. Building all of it
simultaneously with no working end-to-end path is the #1 way this kind of
project stalls. Instead we build in phases where **each phase is a working,
demoable system** before we add the next layer.

### Phase 1 — Core Loop (MVP)
Goal: prove the entire pipeline works, enrollment to attendance to record.
- Auth: login/logout, JWT, single Admin role only (Lecturer/Student roles
  scaffolded but not fully built yet)
- Admin: Add/Edit/Delete Students, Register Fingerprint (enrollment wizard)
- Database: Students, Users, Attendance Records, Device Status (core tables only)
- Firmware: WiFi connect, enroll fingerprint, verify fingerprint, send to API,
  local offline queue + sync
- One attendance flow end-to-end: student enrolls -> places finger -> record
  appears in DB -> shows on a basic admin table
- Basic dashboard: total students, today's attendance count

### Phase 2 — Multi-Role + Academic Structure
- Lecturer and Student roles fully implemented (RBAC enforced)
- Departments, Faculties, Courses, Course Assignments
- Attendance Sessions (start/end session tied to a course + lecturer)
- Manual attendance marking by lecturer
- Student self-service: view own attendance %, history, registered courses

### Phase 3 — Reporting & Analytics
- PDF/Excel/CSV export
- Charts: daily/weekly/monthly, department & course comparison
- Attendance percentage calculation + low-attendance alerts
- Notifications (in-app first; email/SMS later)

### Phase 4 — Hardware Resilience & Ops
- Battery + solar charge monitoring reported from firmware
- Device health monitoring dashboard
- Multiple device support
- Audit logs, backup/restore
- Rate limiting, CSRF/XSS hardening pass

### Phase 5 — Polish
- Dark mode, animations, heatmaps
- QR fallback (optional, only if you want a manual-entry backup path)
- Real-time dashboard updates (WebSocket/polling)

We are starting Phase 1 now.

## 3. Tech Stack (confirmed from your spec)

| Layer | Choice |
|---|---|
| Firmware | ESP32, Arduino IDE (C++), Adafruit Fingerprint library for AS608/R307 |
| Backend | Python 3.11+, Flask, Flask-JWT-Extended, SQLAlchemy |
| Database | MySQL 8 |
| Frontend | HTML5, Bootstrap 5, vanilla JS (upgrade to a framework only if needed later), Chart.js |
| Auth | JWT, bcrypt password hashing |

## 4. Repo Layout

```
attendance-system/
├── backend/
│   ├── app/
│   │   ├── models/       # SQLAlchemy models
│   │   ├── routes/       # Flask blueprints (REST endpoints)
│   │   ├── services/     # business logic, kept out of routes
│   │   └── utils/        # helpers (auth, validation, etc.)
│   ├── config/           # environment-based config classes
│   ├── migrations/       # Alembic migrations
│   └── tests/
├── frontend/
│   ├── templates/        # Jinja2 templates (admin/lecturer/student)
│   └── static/{css,js,img}
├── firmware/
│   ├── src/               # ESP32 .ino / .cpp
│   ├── lib/
│   └── docs/
├── database/               # schema.sql, seed data
├── docs/                   # this file, diagrams, SRS later
└── deployment/             # docker/config for later
```

## 5. Immediate Next Steps

1. Finalize Phase 1 database schema (this session)
2. Build Flask app skeleton + auth (JWT, bcrypt)
3. Build Student CRUD + fingerprint enrollment endpoint (mocked sensor
   response until firmware is ready)
4. Build ESP32 firmware for enroll + verify + offline queue
5. Wire firmware -> API -> DB end to end
6. Minimal admin UI to see it work
