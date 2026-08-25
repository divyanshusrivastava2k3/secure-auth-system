"""Database models — User, Session, LoginAttempt."""
from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    """Registered user account."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    is_active = db.Column(db.Boolean, default=True)

    sessions = db.relationship("UserSession", backref="user", lazy="dynamic")
    login_attempts = db.relationship("LoginAttempt", backref="user", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_active": self.is_active,
        }


class UserSession(db.Model):
    """Active login session (tracks devices / tokens)."""

    __tablename__ = "sessions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    token_jti = db.Column(db.String(64), unique=True, nullable=False, index=True)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(256))
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    last_active = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    is_revoked = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            "id": self.id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_active": self.last_active.isoformat() if self.last_active else None,
            "is_revoked": self.is_revoked,
        }


class LoginAttempt(db.Model):
    """Login attempt log — used for rate-limiting & audit."""

    __tablename__ = "login_attempts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    username_tried = db.Column(db.String(80), nullable=False)
    ip_address = db.Column(db.String(45))
    success = db.Column(db.Boolean, default=False)
    attempted_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
