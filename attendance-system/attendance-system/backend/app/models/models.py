from datetime import datetime
from app.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum("admin", "lecturer", "student", name="user_role"),
                      nullable=False, default="admin")
    full_name = db.Column(db.String(150), nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "role": self.role,
            "full_name": self.full_name,
            "is_active": self.is_active,
        }


class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    student_number = db.Column(db.String(30), unique=True, nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(30))
    fingerprint_id = db.Column(db.Integer, unique=True, nullable=True)
    is_enrolled = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    attendance_records = db.relationship("AttendanceRecord", backref="student", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "student_number": self.student_number,
            "full_name": self.full_name,
            "email": self.email,
            "phone": self.phone,
            "fingerprint_id": self.fingerprint_id,
            "is_enrolled": self.is_enrolled,
        }


class Device(db.Model):
    __tablename__ = "devices"

    id = db.Column(db.Integer, primary_key=True)
    device_uid = db.Column(db.String(64), unique=True, nullable=False)
    label = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(150))
    api_key = db.Column(db.String(255), nullable=False)
    last_seen_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    attendance_records = db.relationship("AttendanceRecord", backref="device", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "device_uid": self.device_uid,
            "label": self.label,
            "location": self.location,
            "last_seen_at": self.last_seen_at.isoformat() if self.last_seen_at else None,
            "is_active": self.is_active,
        }


class Course(db.Model):
    __tablename__ = "courses"

    id = db.Column(db.Integer, primary_key=True)
    module_code = db.Column(db.String(20), unique=True, nullable=False)
    module_name = db.Column(db.String(150), nullable=False)
    lecturer_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    lecturer = db.relationship("User", foreign_keys=[lecturer_id])
    sessions = db.relationship("AttendanceSession", backref="course", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "module_code": self.module_code,
            "module_name": self.module_name,
            "lecturer_id": self.lecturer_id,
            "lecturer_name": self.lecturer.full_name if self.lecturer else None,
        }


class AttendanceSession(db.Model):
    __tablename__ = "attendance_sessions"

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    device_id = db.Column(db.Integer, db.ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    lecturer_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    lecturer = db.relationship("User", foreign_keys=[lecturer_id])
    device = db.relationship("Device", foreign_keys=[device_id])
    attendance_records = db.relationship("AttendanceRecord", backref="session", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "course_id": self.course_id,
            "module_code": self.course.module_code if self.course else None,
            "module_name": self.course.module_name if self.course else None,
            "device_id": self.device_id,
            "lecturer_id": self.lecturer_id,
            "lecturer_name": self.lecturer.full_name if self.lecturer else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "is_active": self.is_active,
        }


class AttendanceRecord(db.Model):
    __tablename__ = "attendance_records"

    id = db.Column(db.BigInteger, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    device_id = db.Column(db.Integer, db.ForeignKey("devices.id"), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey("attendance_sessions.id", ondelete="SET NULL"), nullable=True)
    fingerprint_id = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Enum("present", "late", name="attendance_status"),
                        nullable=False, default="present")
    recorded_at = db.Column(db.DateTime, nullable=False)
    received_at = db.Column(db.DateTime, default=datetime.utcnow)
    synced_offline = db.Column(db.Boolean, nullable=False, default=False)
    battery_percentage = db.Column(db.SmallInteger, nullable=True)
    network_status = db.Column(db.Enum("online", "offline_queued", name="network_status"),
                                 nullable=False, default="online")

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "student_name": self.student.full_name if self.student else None,
            "device_id": self.device_id,
            "session_id": self.session_id,
            "module_code": self.session.course.module_code if self.session and self.session.course else None,
            "module_name": self.session.course.module_name if self.session and self.session.course else None,
            "lecturer_name": self.session.lecturer.full_name if self.session and self.session.lecturer else None,
            "fingerprint_id": self.fingerprint_id,
            "status": self.status,
            "recorded_at": self.recorded_at.isoformat(),
            "received_at": self.received_at.isoformat() if self.received_at else None,
            "synced_offline": self.synced_offline,
            "battery_percentage": self.battery_percentage,
            "network_status": self.network_status,
        }
