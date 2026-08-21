from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from app.extensions import db
from app.models import CourseEnrollment, Course, Student
from app.utils.auth import role_required

enrollment_bp = Blueprint("enrollments", __name__, url_prefix="/api/courses")


@enrollment_bp.post("/<int:course_id>/enroll")
@jwt_required()
@role_required("admin")
def enroll_student(course_id):
    course = Course.query.get_or_404(course_id)
    data = request.get_json(silent=True) or {}
    student_id = data.get("student_id")

    if not student_id:
        return jsonify({"error": "student_id is required"}), 400

    student = Student.query.get(student_id)
    if not student:
        return jsonify({"error": "Student not found"}), 404

    existing = CourseEnrollment.query.filter_by(course_id=course_id, student_id=student_id).first()
    if existing:
        return jsonify({"error": "Student is already enrolled in this course"}), 409

    enrollment = CourseEnrollment(course_id=course_id, student_id=student_id)
    db.session.add(enrollment)
    db.session.commit()
    return jsonify(enrollment.to_dict()), 201


@enrollment_bp.delete("/<int:course_id>/enroll/<int:student_id>")
@jwt_required()
@role_required("admin")
def unenroll_student(course_id, student_id):
    enrollment = CourseEnrollment.query.filter_by(course_id=course_id, student_id=student_id).first_or_404()
    db.session.delete(enrollment)
    db.session.commit()
    return jsonify({"message": "Student unenrolled"}), 200


@enrollment_bp.get("/<int:course_id>/students")
@jwt_required()
@role_required("admin", "lecturer")
def list_enrolled_students(course_id):
    Course.query.get_or_404(course_id)
    enrollments = CourseEnrollment.query.filter_by(course_id=course_id).all()
    return jsonify([e.to_dict() for e in enrollments]), 200
