import secrets
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required

from app.extensions import db
from app.models import Device
from app.utils.auth import role_required

device_bp = Blueprint("devices", __name__, url_prefix="/api/devices")


@device_bp.get("")
@jwt_required()
@role_required("admin")
def list_devices():
    devices = Device.query.all()
    return jsonify([d.to_dict() for d in devices]), 200


@device_bp.post("")
@jwt_required()
@role_required("admin")
def register_device():
    """
    Registers a new ESP32 unit and generates its api_key. The key is
    returned ONCE here — copy it straight into the firmware's config
    (see firmware/src/config.h). It is never returned again by any
    other endpoint.
    """
    data = request.get_json(silent=True) or {}
    device_uid = data.get("device_uid")
    label = data.get("label")

    if not device_uid or not label:
        return jsonify({"error": "device_uid and label are required"}), 400

    if Device.query.filter_by(device_uid=device_uid).first():
        return jsonify({"error": "device_uid already registered"}), 409

    device = Device(
        device_uid=device_uid,
        label=label,
        location=data.get("location"),
        api_key=secrets.token_hex(32),
    )
    db.session.add(device)
    db.session.commit()

    response = device.to_dict()
    response["api_key"] = device.api_key  # only time this is ever exposed
    return jsonify(response), 201
