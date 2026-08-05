"""
Extension instances live here, separate from app/__init__.py, so that
models.py and routes can import `db` without triggering circular imports.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS

db = SQLAlchemy()
jwt = JWTManager()
cors = CORS()
