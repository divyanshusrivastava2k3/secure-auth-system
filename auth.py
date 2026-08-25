"""Authentication helpers — password hashing, JWT creation & verification."""
import uuid
from datetime import datetime, timezone
from functools import wraps

import bcrypt
import jwt
from flask import current_app, jsonify, request

from models import LoginAttempt, User, UserSession, db


# ── Password helpers ────────────────────────────────────────────────────────
def hash_password(plain: str) -> str:
    """Hash a plaintext password with bcrypt (auto-salted)."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def check_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def validate_password_strength(password: str) -> list[str]:
    """Return a list of policy violations (empty = valid)."""
    errors = []
    min_len = current_app.config["MIN_PASSWORD_LENGTH"]
    if len(password) < min_len:
        errors.append(f"Password must be at least {min_len} characters.")
    if not any(c.isupper() for c in password):
        errors.append("Password must contain at least one uppercase letter.")
    if not any(c.islower() for c in password):
        errors.append("Password must contain at least one lowercase letter.")
    if not any(c.isdigit() for c in password):
        errors.append("Password must contain at least one digit.")
    if not any(c in "!@#$%^&*()-_=+[]{}|;:',.<>?/`~" for c in password):
        errors.append("Password must contain at least one special character.")
    return errors


# ── JWT helpers ─────────────────────────────────────────────────────────────
def _create_token(user_id: int, token_type: str, expires_delta) -> tuple[str, str]:
    """Create a signed JWT; returns (token_string, jti)."""
    jti = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "type": token_type,
        "jti": jti,
        "iat": now,
        "exp": now + expires_delta,
    }
    token = jwt.encode(payload, current_app.config["JWT_SECRET_KEY"], algorithm="HS256")
    return token, jti


def create_access_token(user_id: int) -> tuple[str, str]:
    return _create_token(user_id, "access", current_app.config["JWT_ACCESS_TOKEN_EXPIRES"])


def create_refresh_token(user_id: int) -> tuple[str, str]:
    return _create_token(user_id, "refresh", current_app.config["JWT_REFRESH_TOKEN_EXPIRES"])


def decode_token(token: str) -> dict | None:
    """Decode and verify a JWT; returns payload or None."""
    try:
        return jwt.decode(
            token,
            current_app.config["JWT_SECRET_KEY"],
            algorithms=["HS256"],
        )
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


# ── Login-attempt rate limiter ──────────────────────────────────────────────
def is_rate_limited(username: str, ip: str) -> bool:
    """Check if the account or IP is temporarily locked out."""
    max_attempts = current_app.config["MAX_LOGIN_ATTEMPTS"]
    lockout_mins = current_app.config["LOGIN_LOCKOUT_MINUTES"]
    from datetime import timedelta

    cutoff = datetime.now(timezone.utc) - timedelta(minutes=lockout_mins)
    recent_failures = LoginAttempt.query.filter(
        LoginAttempt.username_tried == username,
        LoginAttempt.success == False,  # noqa: E712
        LoginAttempt.attempted_at >= cutoff,
    ).count()
    return recent_failures >= max_attempts


def log_attempt(username: str, user_id: int | None, ip: str, success: bool):
    """Record a login attempt."""
    attempt = LoginAttempt(
        user_id=user_id,
        username_tried=username,
        ip_address=ip,
        success=success,
    )
    db.session.add(attempt)
    db.session.commit()


# ── Decorator: require valid JWT ────────────────────────────────────────────
def login_required(f):
    """Protect a route — injects `current_user` into kwargs."""

    @wraps(f)
    def wrapper(*args, **kwargs):
        token = None
        # Accept token from cookie or Authorization header
        if "access_token" in request.cookies:
            token = request.cookies.get("access_token")
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]

        if not token:
            if request.is_json or request.path.startswith("/api/"):
                return jsonify({"error": "Authentication required."}), 401
            from flask import redirect, url_for
            return redirect(url_for("main.login_page"))

        payload = decode_token(token)
        if not payload or payload.get("type") != "access":
            if request.is_json or request.path.startswith("/api/"):
                return jsonify({"error": "Invalid or expired token."}), 401
            from flask import redirect, url_for
            return redirect(url_for("main.login_page"))

        # Check session not revoked
        session_obj = UserSession.query.filter_by(
            token_jti=payload["jti"], is_revoked=False
        ).first()
        if not session_obj:
            if request.is_json or request.path.startswith("/api/"):
                return jsonify({"error": "Session revoked."}), 401
            from flask import redirect, url_for
            return redirect(url_for("main.login_page"))

        user = User.query.get(int(payload["sub"]))
        if not user or not user.is_active:
            if request.is_json or request.path.startswith("/api/"):
                return jsonify({"error": "Account not found or disabled."}), 401
            from flask import redirect, url_for
            return redirect(url_for("main.login_page"))

        # Update last_active
        session_obj.last_active = datetime.now(timezone.utc)
        db.session.commit()

        kwargs["current_user"] = user
        kwargs["current_session"] = session_obj
        return f(*args, **kwargs)

    return wrapper
