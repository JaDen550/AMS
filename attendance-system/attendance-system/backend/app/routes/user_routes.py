from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from app.extensions import db
from app.models import User
from app.utils.auth import role_required, hash_password

user_bp = Blueprint("users", __name__, url_prefix="/api/users")


@user_bp.get("")
@jwt_required()
@role_required("admin")
def list_users():
    """Optional ?role=lecturer filter — handy for populating a lecturer picker."""
    query = User.query
    role = request.args.get("role")
    if role:
        query = query.filter_by(role=role)
    users = query.order_by(User.full_name).all()
    return jsonify([u.to_dict() for u in users]), 200


@user_bp.post("")
@jwt_required()
@role_required("admin")
def create_user():
    """
    Admin creates lecturer (or additional admin) accounts. Student
    accounts are created separately via /api/students — students are
    primarily identified by enrollment data, not login credentials,
    so they're deliberately a different resource in Phase 1/2.
    """
    data = request.get_json(silent=True) or {}
    required = ["email", "password", "full_name", "role"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 400

    if data["role"] not in ("admin", "lecturer"):
        return jsonify({"error": "role must be 'admin' or 'lecturer' (use /api/students for students)"}), 400

    if User.query.filter_by(email=data["email"].strip().lower()).first():
        return jsonify({"error": "A user with this email already exists"}), 409

    user = User(
        email=data["email"].strip().lower(),
        password_hash=hash_password(data["password"]),
        role=data["role"],
        full_name=data["full_name"],
    )
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201
