from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from app.extensions import db
from app.models import Student
from app.utils.auth import role_required

student_bp = Blueprint("students", __name__, url_prefix="/api/students")


@student_bp.get("")
@jwt_required()
@role_required("admin", "lecturer")
def list_students():
    students = Student.query.order_by(Student.full_name).all()
    return jsonify([s.to_dict() for s in students]), 200


@student_bp.get("/<int:student_id>")
@jwt_required()
@role_required("admin", "lecturer")
def get_student(student_id):
    student = Student.query.get_or_404(student_id)
    return jsonify(student.to_dict()), 200


@student_bp.post("")
@jwt_required()
@role_required("admin")
def create_student():
    data = request.get_json(silent=True) or {}
    required = ["student_number", "full_name"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    if Student.query.filter_by(student_number=data["student_number"]).first():
        return jsonify({"error": "student_number already exists"}), 409

    student = Student(
        student_number=data["student_number"],
        full_name=data["full_name"],
        email=data.get("email"),
        phone=data.get("phone"),
    )
    db.session.add(student)
    db.session.commit()
    return jsonify(student.to_dict()), 201


@student_bp.put("/<int:student_id>")
@jwt_required()
@role_required("admin")
def update_student(student_id):
    student = Student.query.get_or_404(student_id)
    data = request.get_json(silent=True) or {}

    for field in ["full_name", "email", "phone"]:
        if field in data:
            setattr(student, field, data[field])

    db.session.commit()
    return jsonify(student.to_dict()), 200


@student_bp.delete("/<int:student_id>")
@jwt_required()
@role_required("admin")
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    db.session.delete(student)
    db.session.commit()
    return jsonify({"message": "Student deleted"}), 200


@student_bp.post("/<int:student_id>/enroll-fingerprint")
@jwt_required()
@role_required("admin")
def enroll_fingerprint(student_id):
    """
    Phase 1 stub: assigns a fingerprint_id to the student record so the
    rest of the system (attendance matching, UI, reports) can be built
    and tested before the real ESP32 enrollment flow is wired up.

    In production this endpoint is called BY the device/firmware once a
    physical enrollment succeeds on the AS608/R307 sensor, passing back
    the sensor's real template slot number as `fingerprint_id`. Right
    now it accepts a fingerprint_id directly in the request body so you
    can test the rest of the app without hardware in hand yet.
    """
    student = Student.query.get_or_404(student_id)
    data = request.get_json(silent=True) or {}
    fingerprint_id = data.get("fingerprint_id")

    if fingerprint_id is None:
        return jsonify({"error": "fingerprint_id is required"}), 400

    existing = Student.query.filter_by(fingerprint_id=fingerprint_id).first()
    if existing and existing.id != student.id:
        return jsonify({"error": f"fingerprint_id already assigned to {existing.full_name}"}), 409

    student.fingerprint_id = fingerprint_id
    student.is_enrolled = True
    db.session.commit()
    return jsonify(student.to_dict()), 200
