from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from app.extensions import db
from app.models import Course, User
from app.utils.auth import role_required

course_bp = Blueprint("courses", __name__, url_prefix="/api/courses")


@course_bp.get("")
@jwt_required()
@role_required("admin", "lecturer")
def list_courses():
    courses = Course.query.order_by(Course.module_code).all()
    return jsonify([c.to_dict() for c in courses]), 200


@course_bp.get("/<int:course_id>")
@jwt_required()
@role_required("admin", "lecturer")
def get_course(course_id):
    course = Course.query.get_or_404(course_id)
    return jsonify(course.to_dict()), 200


@course_bp.post("")
@jwt_required()
@role_required("admin")
def create_course():
    data = request.get_json(silent=True) or {}
    required = ["module_code", "module_name"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    if Course.query.filter_by(module_code=data["module_code"]).first():
        return jsonify({"error": "module_code already exists"}), 409

    lecturer_id = data.get("lecturer_id")
    if lecturer_id is not None:
        lecturer = User.query.filter_by(id=lecturer_id, role="lecturer").first()
        if not lecturer:
            return jsonify({"error": "lecturer_id does not match an existing lecturer"}), 400

    course = Course(
        module_code=data["module_code"],
        module_name=data["module_name"],
        lecturer_id=lecturer_id,
    )
    db.session.add(course)
    db.session.commit()
    return jsonify(course.to_dict()), 201


@course_bp.put("/<int:course_id>")
@jwt_required()
@role_required("admin")
def update_course(course_id):
    course = Course.query.get_or_404(course_id)
    data = request.get_json(silent=True) or {}

    if "module_name" in data:
        course.module_name = data["module_name"]

    if "lecturer_id" in data:
        lecturer_id = data["lecturer_id"]
        if lecturer_id is not None:
            lecturer = User.query.filter_by(id=lecturer_id, role="lecturer").first()
            if not lecturer:
                return jsonify({"error": "lecturer_id does not match an existing lecturer"}), 400
        course.lecturer_id = lecturer_id

    db.session.commit()
    return jsonify(course.to_dict()), 200


@course_bp.delete("/<int:course_id>")
@jwt_required()
@role_required("admin")
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    db.session.delete(course)
    db.session.commit()
    return jsonify({"message": "Course deleted"}), 200
