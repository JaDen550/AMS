# Solar-Powered Biometric Attendance Management System

Building a full
biometric attendance system for Sierra Leone educational institutions:
ESP32 + AS608/R307 fingerprint sensor (solar-powered in production),
Flask REST API, MySQL, and a role-based web app (Admin / Lecturer / Student).

## Where things stand

Phase 1 (core loop) is scaffolded:
- Database schema — `database/schema.sql`
- Backend API — `backend/` (Flask, JWT auth, student CRUD, device
  registration, attendance ingest + offline sync support)
- Firmware — `firmware/` (ESP32 WiFi + fingerprint enroll/verify +
  offline queue + sync)

Not built yet, by design — see `docs/ARCHITECTURE.md` for the full
phase plan: Lecturer/Student portals, courses/departments, reports,
notifications, battery/solar dashboards, multi-device support.

## Getting started

1. Backend setup: `backend/README.md`
2. Firmware setup: `firmware/README.md`
3. Full architecture and phase roadmap: `docs/ARCHITECTURE.md`

## Repo layout

```
attendance-system/
├── backend/       Flask REST API
├── frontend/       web app (not started yet — Phase 1 uses API + curl/Postman for now)
├── firmware/      ESP32 firmware
├── database/       schema.sql
├── docs/           architecture, phase plan, diagrams (later)
└── deployment/     (later)
```
