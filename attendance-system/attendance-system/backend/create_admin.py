"""
One-off script to create the first admin account with a proper bcrypt hash.
Run once after the database schema is loaded:

    python create_admin.py

Do this instead of relying on the placeholder INSERT in database/schema.sql —
that placeholder hash will not pass check_password() as-is.
"""
import getpass
from app import create_app
from app.extensions import db
from app.models import User
from app.utils.auth import hash_password

app = create_app()

with app.app_context():
    email = input("Admin email: ").strip().lower()
    full_name = input("Admin full name: ").strip()
    password = getpass.getpass("Admin password: ")

    existing = User.query.filter_by(email=email).first()
    if existing:
        print(f"A user with email {email} already exists (id={existing.id}). Aborting.")
    else:
        user = User(
            email=email,
            full_name=full_name,
            role="admin",
            password_hash=hash_password(password),
        )
        db.session.add(user)
        db.session.commit()
        print(f"Admin user created: {email} (id={user.id})")
