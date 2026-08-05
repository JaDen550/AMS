# Backend — Flask API

## Setup (Windows 10/11, but same idea on any OS)

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt
copy .env.example .env         # then edit .env with real values
```

1. Install MySQL locally (or use XAMPP/WAMP if that's easier on Windows).
2. Load the schema:
   ```bash
   mysql -u root -p < ../database/schema.sql
   ```
3. Create your admin user with a real password hash:
   ```bash
   python create_admin.py
   ```
4. Run the server:
   ```bash
   python run.py
   ```
   API is now live at `http://localhost:5000` — and reachable from the ESP32
   at `http://<your-laptop-LAN-IP>:5000` as long as both are on the same WiFi.

## Quick smoke test

```bash
curl http://localhost:5000/api/health
# {"status": "ok"}

curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"admin@example.com\",\"password\":\"yourpassword\"}"
```

## Endpoints implemented so far (Phase 1)

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | /api/auth/login | none | Get JWT |
| GET | /api/auth/me | JWT | Current user info |
| GET | /api/students | JWT (admin/lecturer) | List students |
| POST | /api/students | JWT (admin) | Create student |
| PUT | /api/students/:id | JWT (admin) | Update student |
| DELETE | /api/students/:id | JWT (admin) | Delete student |
| POST | /api/students/:id/enroll-fingerprint | JWT (admin) | Link fingerprint_id to student |
| POST | /api/devices | JWT (admin) | Register a new ESP32 device |
| GET | /api/devices | JWT (admin) | List devices |
| POST | /api/attendance | Device API key | Device submits an attendance record |
| GET | /api/attendance | JWT (admin/lecturer) | List records, filter by student_id/date |
| GET | /api/attendance/today-summary | JWT (admin/lecturer) | Dashboard counts |

Everything else in the original spec (Lecturer/Student portals, courses,
reports, notifications, etc.) is intentionally not built yet — see
`docs/ARCHITECTURE.md` for the phase plan.
