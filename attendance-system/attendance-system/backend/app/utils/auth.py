from functools import wraps
import bcrypt
from flask import jsonify, request, current_app
from flask_jwt_extended import get_jwt, verify_jwt_in_request


def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def check_password(plain_password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))


def role_required(*allowed_roles):
    """
    Route decorator restricting access to specific roles, e.g.
    @role_required("admin")
    @role_required("admin", "lecturer")
    Must be used AFTER @jwt_required() in the decorator stack, or it will
    call verify_jwt_in_request() itself if no request context has been
    verified yet.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get("role") not in allowed_roles:
                return jsonify({"error": "Forbidden: insufficient role"}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def device_key_required(fn):
    """
    Authenticates the ESP32 device itself — NOT a human user, so this
    intentionally does not use JWT. The device sends a static API key
    (provisioned when the device row is created) in a header on every
    request. Rotate a device's key by updating its `api_key` column if
    a unit is ever lost or compromised.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        from app.models import Device  # local import avoids circular import

        header_name = current_app.config.get("DEVICE_API_KEY_HEADER", "X-Device-Key")
        provided_key = request.headers.get(header_name)

        if not provided_key:
            return jsonify({"error": f"Missing {header_name} header"}), 401

        device = Device.query.filter_by(api_key=provided_key, is_active=True).first()
        if not device:
            return jsonify({"error": "Invalid or inactive device key"}), 401

        request.device = device  # stash for the route handler
        return fn(*args, **kwargs)
    return wrapper
