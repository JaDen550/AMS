from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from app.extensions import db
from app.models import AttendanceRecord, Student
from app.utils.auth import role_required, device_key_required

attendance_bp = Blueprint("attendance", __name__, url_prefix="/api/attendance")


@attendance_bp.post("")
@device_key_required
def submit_attendance():
    """
    Called BY the ESP32 firmware — once for each real-time match, and
    again (with synced_offline=True) for each record that was queued
    locally while the device had no network connection.
    """
    data = request.get_json(silent=True) or {}
    fingerprint_id = data.get("fingerprint_id")
    recorded_at_raw = data.get("recorded_at")  # ISO8601 string from device clock

    if fingerprint_id is None or not recorded_at_raw:
        return jsonify({"error": "fingerprint_id and recorded_at are required"}), 400

    student = Student.query.filter_by(fingerprint_id=fingerprint_id).first()
    if not student:
        return jsonify({"error": "No student matches this fingerprint_id"}), 404

    try:
        recorded_at = datetime.fromisoformat(recorded_at_raw)
    except ValueError:
        return jsonify({"error": "recorded_at must be ISO8601"}), 400

    record = AttendanceRecord(
        student_id=student.id,
        device_id=request.device.id,
        fingerprint_id=fingerprint_id,
        status=data.get("status", "present"),
        recorded_at=recorded_at,
        synced_offline=bool(data.get("synced_offline", False)),
        battery_percentage=data.get("battery_percentage"),
        network_status=data.get("network_status", "online"),
    )
    db.session.add(record)

    request.device.last_seen_at = datetime.utcnow()
    db.session.commit()

    return jsonify(record.to_dict()), 201


@attendance_bp.get("")
@jwt_required()
@role_required("admin", "lecturer")
def list_attendance():
    """Basic listing with optional ?student_id= and ?date=YYYY-MM-DD filters."""
    query = AttendanceRecord.query

    student_id = request.args.get("student_id")
    if student_id:
        query = query.filter_by(student_id=student_id)

    date_str = request.args.get("date")
    if date_str:
        try:
            day = datetime.strptime(date_str, "%Y-%m-%d").date()
            query = query.filter(db.func.date(AttendanceRecord.recorded_at) == day)
        except ValueError:
            return jsonify({"error": "date must be YYYY-MM-DD"}), 400

    records = query.order_by(AttendanceRecord.recorded_at.desc()).limit(500).all()
    return jsonify([r.to_dict() for r in records]), 200


@attendance_bp.get("/today-summary")
@jwt_required()
@role_required("admin", "lecturer")
def today_summary():
    today = datetime.utcnow().date()
    total_students = Student.query.filter_by(is_enrolled=True).count()
    present_today = (
        AttendanceRecord.query
        .filter(db.func.date(AttendanceRecord.recorded_at) == today)
        .distinct(AttendanceRecord.student_id)
        .count()
    )
    return jsonify({
        "date": today.isoformat(),
        "total_enrolled_students": total_students,
        "present_today": present_today,
        "absent_today": max(total_students - present_today, 0),
    }), 200
