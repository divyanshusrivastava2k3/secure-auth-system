"""Flask routes — web pages + JSON API endpoints."""
from datetime import datetime, timezone

from flask import (
    Blueprint,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    url_for,
)

from auth import (
    check_password,
    create_access_token,
    create_refresh_token,
    hash_password,
    is_rate_limited,
    log_attempt,
    login_required,
    validate_password_strength,
    decode_token,
)
from models import LoginAttempt, User, UserSession, db

bp = Blueprint("main", __name__)


# ── Page routes ─────────────────────────────────────────────────────────────
@bp.route("/")
def index():
    return redirect(url_for("main.login_page"))


@bp.route("/login")
def login_page():
    return render_template("login.html")


@bp.route("/register")
def register_page():
    return render_template("register.html")


@bp.route("/dashboard")
@login_required
def dashboard_page(current_user=None, current_session=None):
    total_users = User.query.count()
    total_sessions = UserSession.query.filter_by(
        user_id=current_user.id, is_revoked=False
    ).count()
    total_logins = LoginAttempt.query.filter_by(
        user_id=current_user.id, success=True
    ).count()
    failed_attempts = LoginAttempt.query.filter_by(
        username_tried=current_user.username, success=False
    ).count()
    return render_template(
        "dashboard.html",
        user=current_user,
        stats={
            "total_users": total_users,
            "active_sessions": total_sessions,
            "total_logins": total_logins,
            "failed_attempts": failed_attempts,
        },
        current_jti=current_session.token_jti,
    )


@bp.route("/sessions")
@login_required
def sessions_page(current_user=None, current_session=None):
    sessions = (
        UserSession.query.filter_by(user_id=current_user.id)
        .order_by(UserSession.created_at.desc())
        .limit(50)
        .all()
    )
    return render_template(
        "sessions.html",
        user=current_user,
        sessions=sessions,
        current_jti=current_session.token_jti,
    )


@bp.route("/change-password")
@login_required
def change_password_page(current_user=None, current_session=None):
    return render_template("change_password.html", user=current_user)


# ── API routes ──────────────────────────────────────────────────────────────
@bp.route("/api/register", methods=["POST"])
def api_register():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip().lower()
    email = data.get("email", "").strip().lower()
    full_name = data.get("full_name", "").strip()
    password = data.get("password", "")

    # Validation
    if not all([username, email, full_name, password]):
        return jsonify({"error": "All fields are required."}), 400
    if len(username) < 3 or len(username) > 80:
        return jsonify({"error": "Username must be 3-80 characters."}), 400
    if "@" not in email or "." not in email:
        return jsonify({"error": "Invalid email address."}), 400

    pw_errors = validate_password_strength(password)
    if pw_errors:
        return jsonify({"error": pw_errors[0], "password_errors": pw_errors}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({"error": "Username already taken."}), 409
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered."}), 409

    user = User(
        username=username,
        email=email,
        full_name=full_name,
        password_hash=hash_password(password),
    )
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "Registration successful! Please log in.", "user": user.to_dict()}), 201


@bp.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip().lower()
    password = data.get("password", "")
    ip = request.remote_addr or "unknown"

    if not username or not password:
        return jsonify({"error": "Username and password are required."}), 400

    # Rate-limit check
    if is_rate_limited(username, ip):
        return jsonify({
            "error": "Too many failed attempts. Account temporarily locked. Try again later."
        }), 429

    user = User.query.filter_by(username=username).first()

    if not user or not check_password(password, user.password_hash):
        log_attempt(username, user.id if user else None, ip, False)
        return jsonify({"error": "Invalid username or password."}), 401

    if not user.is_active:
        return jsonify({"error": "Account is disabled."}), 403

    # Success — create tokens
    access_token, access_jti = create_access_token(user.id)
    refresh_token, refresh_jti = create_refresh_token(user.id)

    # Save session
    session_obj = UserSession(
        user_id=user.id,
        token_jti=access_jti,
        ip_address=ip,
        user_agent=request.headers.get("User-Agent", "")[:256],
    )
    db.session.add(session_obj)
    log_attempt(username, user.id, ip, True)

    resp = make_response(jsonify({
        "message": "Login successful!",
        "user": user.to_dict(),
        "access_token": access_token,
        "refresh_token": refresh_token,
    }))
    resp.set_cookie(
        "access_token", access_token,
        httponly=True, samesite="Lax", max_age=1800, path="/",
    )
    resp.set_cookie(
        "refresh_token", refresh_token,
        httponly=True, samesite="Lax", max_age=604800, path="/",
    )
    return resp, 200


@bp.route("/api/refresh", methods=["POST"])
def api_refresh():
    token = request.cookies.get("refresh_token")
    if not token:
        data = request.get_json(silent=True) or {}
        token = data.get("refresh_token")
    if not token:
        return jsonify({"error": "Refresh token required."}), 401

    payload = decode_token(token)
    if not payload or payload.get("type") != "refresh":
        return jsonify({"error": "Invalid or expired refresh token."}), 401

    user = User.query.get(int(payload["sub"]))
    if not user or not user.is_active:
        return jsonify({"error": "User not found or disabled."}), 401

    # Revoke old sessions with this refresh
    access_token, access_jti = create_access_token(user.id)

    session_obj = UserSession(
        user_id=user.id,
        token_jti=access_jti,
        ip_address=request.remote_addr,
        user_agent=request.headers.get("User-Agent", "")[:256],
    )
    db.session.add(session_obj)
    db.session.commit()

    resp = make_response(jsonify({
        "message": "Token refreshed.",
        "access_token": access_token,
    }))
    resp.set_cookie(
        "access_token", access_token,
        httponly=True, samesite="Lax", max_age=1800, path="/",
    )
    return resp, 200


@bp.route("/api/logout", methods=["POST"])
@login_required
def api_logout(current_user=None, current_session=None):
    current_session.is_revoked = True
    db.session.commit()
    resp = make_response(jsonify({"message": "Logged out successfully."}))
    resp.delete_cookie("access_token", path="/")
    resp.delete_cookie("refresh_token", path="/")
    return resp, 200


@bp.route("/api/revoke-session/<int:session_id>", methods=["POST"])
@login_required
def api_revoke_session(session_id, current_user=None, current_session=None):
    session_obj = UserSession.query.filter_by(
        id=session_id, user_id=current_user.id
    ).first()
    if not session_obj:
        return jsonify({"error": "Session not found."}), 404
    session_obj.is_revoked = True
    db.session.commit()
    return jsonify({"message": "Session revoked."})


@bp.route("/api/revoke-all", methods=["POST"])
@login_required
def api_revoke_all(current_user=None, current_session=None):
    UserSession.query.filter(
        UserSession.user_id == current_user.id,
        UserSession.token_jti != current_session.token_jti,
    ).update({"is_revoked": True})
    db.session.commit()
    return jsonify({"message": "All other sessions revoked."})


@bp.route("/api/change-password", methods=["POST"])
@login_required
def api_change_password(current_user=None, current_session=None):
    data = request.get_json(silent=True) or {}
    current_pw = data.get("current_password", "")
    new_pw = data.get("new_password", "")

    if not current_pw or not new_pw:
        return jsonify({"error": "Both current and new password are required."}), 400

    if not check_password(current_pw, current_user.password_hash):
        return jsonify({"error": "Current password is incorrect."}), 401

    pw_errors = validate_password_strength(new_pw)
    if pw_errors:
        return jsonify({"error": pw_errors[0], "password_errors": pw_errors}), 400

    current_user.password_hash = hash_password(new_pw)

    # Revoke all other sessions for safety
    UserSession.query.filter(
        UserSession.user_id == current_user.id,
        UserSession.token_jti != current_session.token_jti,
    ).update({"is_revoked": True})

    db.session.commit()
    return jsonify({"message": "Password changed! All other sessions revoked."})


@bp.route("/api/me")
@login_required
def api_me(current_user=None, current_session=None):
    return jsonify({"user": current_user.to_dict()})
