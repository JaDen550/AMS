from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

from app.extensions import db
from app.models import AttendanceSession, Course, Device, AttendanceRecord, CourseEnrollment, Student
from app.utils.auth import role_required

session_bp = Blueprint("sessions", __name__, url_prefix="/api/sessions")


@session_bp.post("/start")
@jwt_required()
@role_required("admin", "lecturer")
def start_session():
    data = request.get_json(silent=True) or {}
    course_id = data.get("course_id")
    device_id = data.get("device_id")

    if not course_id or not device_id:
        return jsonify({"error": "course_id and device_id are required"}), 400

    course = Course.query.get(course_id)
    if not course:
        return jsonify({"error": "Course not found"}), 404

    device = Device.query.get(device_id)
    if not device:
        return jsonify({"error": "Device not found"}), 404

    claims = get_jwt()
    current_user_id = int(get_jwt_identity())
    if claims.get("role") == "lecturer" and course.lecturer_id != current_user_id:
        return jsonify({"error": "You are not the assigned lecturer for this course"}), 403

    existing_active = AttendanceSession.query.filter_by(device_id=device_id, is_active=True).all()
    for s in existing_active:
        s.is_active = False
        s.ended_at = datetime.utcnow()

    lecturer_id = course.lecturer_id if course.lecturer_id else current_user_id
    session = AttendanceSession(
        course_id=course_id,
        device_id=device_id,
        lecturer_id=lecturer_id,
    )
    db.session.add(session)
    db.session.commit()
    return jsonify(session.to_dict()), 201


@session_bp.post("/<int:session_id>/end")
@jwt_required()
@role_required("admin", "lecturer")
def end_session(session_id):
    session = AttendanceSession.query.get_or_404(session_id)

    claims = get_jwt()
    current_user_id = int(get_jwt_identity())
    if claims.get("role") == "lecturer" and session.lecturer_id != current_user_id:
        return jsonify({"error": "You did not start this session"}), 403

    session.is_active = False
    session.ended_at = datetime.utcnow()
    db.session.commit()
    return jsonify(session.to_dict()), 200


@session_bp.get("")
@jwt_required()
@role_required("admin", "lecturer")
def list_sessions():
    query = AttendanceSession.query

    active_param = request.args.get("active")
    if active_param is not None:
        query = query.filter_by(is_active=(active_param.lower() == "true"))

    device_id = request.args.get("device_id")
    if device_id:
        query = query.filter_by(device_id=device_id)

    sessions = query.order_by(AttendanceSession.started_at.desc()).limit(100).all()
    return jsonify([s.to_dict() for s in sessions]), 200


@session_bp.post("/<int:session_id>/mark-attendance")
@jwt_required()
@role_required("admin", "lecturer")
def mark_attendance(session_id):
    """
    Manual fallback for when a fingerprint scan genuinely fails (dirty
    sensor, minor cut, misread) but the lecturer can see the student is
    physically present. Lecturer/admin only — never reachable by a
    student. Every use is stamped with is_manual=True and marked_by,
    so it's fully auditable: anyone reviewing attendance data can see
    exactly which records were manually entered and by whom.
    """
    session = AttendanceSession.query.get_or_404(session_id)

    claims = get_jwt()
    current_user_id = int(get_jwt_identity())
    if claims.get("role") == "lecturer" and session.lecturer_id != current_user_id:
        return jsonify({"error": "You are not running this session"}), 403

    if not session.is_active:
        return jsonify({"error": "This session has already ended"}), 400

    data = request.get_json(silent=True) or {}
    student_id = data.get("student_id")
    if not student_id:
        return jsonify({"error": "student_id is required"}), 400

    student = Student.query.get(student_id)
    if not student:
        return jsonify({"error": "Student not found"}), 404

    already_marked = AttendanceRecord.query.filter_by(
        student_id=student_id, session_id=session_id
    ).first()
    if already_marked:
        return jsonify({"error": "This student already has an attendance record for this session"}), 409

    record = AttendanceRecord(
        student_id=student_id,
        device_id=session.device_id,
        session_id=session_id,
        fingerprint_id=student.fingerprint_id,
        status=data.get("status", "present"),
        is_manual=True,
        marked_by=current_user_id,
        recorded_at=datetime.utcnow(),
        network_status="online",
    )
    db.session.add(record)
    db.session.commit()
    return jsonify(record.to_dict()), 201
