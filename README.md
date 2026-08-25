# 🔐 Secure Authentication System (JWT + bcrypt + Flask)

![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.x-000000?style=for-the-badge&logo=flask&logoColor=white)
![JWT](https://img.shields.io/badge/JWT-PyJWT-000000?style=for-the-badge&logo=jsonwebtokens&logoColor=white)
![Security](https://img.shields.io/badge/Security-bcrypt-10b981?style=for-the-badge)
![Database](https://img.shields.io/badge/SQLite%20%2f%20PostgreSQL-SQLAlchemy-4479A1?style=for-the-badge&logo=sqlite&logoColor=white)
![UI](https://img.shields.io/badge/UI-Glassmorphism-7c3aed?style=for-the-badge)

> A production-grade **Secure Authentication & Session Management System** built with Python Flask, PyJWT, bcrypt password hashing, and an interactive **Glassmorphism web interface**. Built with enterprise security patterns including access/refresh tokens, brute-force rate limiting, device session tracking, and remote session revocation.

---

## 📸 Screenshots Showcase

### 🏠 1. User Registration & Password Strength Meter
![Register Screen](docs/01_register.png)

*Real-time password policy validation with dynamic strength meter.*

![Register Form Filled](docs/02_register_filled.png)

---

### 🔑 2. Secure Login Screen
![Login Screen](docs/03_login.png)

---

### 📊 3. User Dashboard
![Dashboard](docs/04_dashboard.png)

*Security metrics, account stats, profile details, and quick security actions.*

---

### 📱 4. Active Session Management
![Session Management](docs/05_sessions.png)

*Device tracking, IP logging, user-agent parsing, and one-click remote session revocation.*

---

### 🔒 5. Password Update Screen
![Change Password](docs/06_change_password.png)

---

## ✨ Features

| Category | Feature | Description |
|---|---|---|
| 🔑 **Authentication** | **JWT Access & Refresh Tokens** | Dual-token pattern (`HS256` signed JWTs) stored safely in `HttpOnly` + `SameSite` cookies |
| 🛡️ **Password Security** | **bcrypt Hashing** | Passwords automatically salted and hashed with `bcrypt` (work factor 12) |
| 📏 **Policy Enforcement** | **Strength Meter** | Requires 8+ chars, uppercase, lowercase, digit, and special character |
| 🚫 **Brute-Force Protection** | **Rate Limiting** | Temporary IP/account lockout after 5 consecutive failed login attempts |
| 📱 **Session Control** | **Device Tracking** | Every login records IP address, User-Agent, and token JTI |
| ❌ **Remote Revocation** | **Session Kill** | Users can view active sessions and revoke individual devices or all other devices |
| 🎨 **Frontend** | **Glassmorphism UI** | Modern frosted-glass aesthetic with CSS backdrop blurs, animated gradient orbs & responsive layout |
| 🗄️ **Database Support** | **SQLite & PostgreSQL** | Default zero-config SQLite for local demo; seamless PostgreSQL switch via `DATABASE_URL` |

---

## 🛠️ Tech Stack

| Component | Technology Used |
|---|---|
| **Backend Framework** | Python **Flask** (Blueprint architecture) |
| **ORM / Database** | **SQLAlchemy** (SQLite local fallback / PostgreSQL compatible) |
| **Authentication** | **PyJWT** (JSON Web Token encode/decode/verification) |
| **Password Hashing** | **bcrypt** |
| **Frontend UI** | HTML5, CSS3 Glassmorphism (`backdrop-filter`), Vanilla JS (ES6 `fetch`) |

---

## 🧭 Security Architecture & Token Flow

```
                           ┌──────────────────────────────────────────────┐
                           │                 Client (Web)                 │
                           └──────────────────────┬───────────────────────┘
                                                  │
                            POST /api/login       │ (credentials)
                           ──────────────────────►│
                                                  ▼
                           ┌──────────────────────────────────────────────┐
                           │               Flask App Server               │
                           │                                              │
                           │  1. Check rate limit (LoginAttempt log)      │
                           │  2. Verify bcrypt hash (User.password_hash)   │
                           │  3. Generate JWT Access & Refresh Tokens      │
                           │  4. Save UserSession (token_jti, IP, UA)     │
                           └──────────────────────┬───────────────────────┘
                                                  │
                            Set-Cookie:           │
                            access_token (HttpOnly)
                            refresh_token(HttpOnly)
                           ◄──────────────────────┘
                                                  │
                            GET /dashboard        │ (HttpOnly Cookie)
                           ──────────────────────►│
                                                  ▼
                           ┌──────────────────────────────────────────────┐
                           │          login_required Decorator            │
                           │  1. Verify JWT signature & expiration        │
                           │  2. Query UserSession by JTI (is_revoked?)   │
                           │  3. Verify User is active                     │
                           └──────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
secure-auth-system/
├── app.py                 # App factory & server entry point
├── config.py              # Environment configuration & JWT parameters
├── models.py              # SQLAlchemy models (User, UserSession, LoginAttempt)
├── auth.py                # Security logic (bcrypt hashing, JWT tokens, login_required decorator)
├── routes.py              # Web page views & REST API endpoints
├── requirements.txt       # Python dependencies
├── .gitignore             # Git ignore rules
├── templates/             # Jinja2 HTML templates with Glassmorphism styling
│   ├── base.html          # Base layout shell & header/footer
│   ├── login.html         # Login page
│   ├── register.html      # Registration page with strength meter
│   ├── dashboard.html     # Security dashboard & stats
│   ├── sessions.html      # Active session management table
│   └── change_password.html # Password update view
├── static/
│   ├── style.css          # Glassmorphism CSS design system
│   └── main.js            # Frontend API client & interactive controls
└── docs/                  # Application screenshots
```

---

## 🚀 Quickstart Guide

### Prerequisites
- **Python 3.9+** installed

### Installation & Setup

```bash
# 1. Clone repository
git clone https://github.com/divyanshusrivastava2k3/secure-auth-system.git
cd secure-auth-system

# 2. Create virtual environment
python -m venv .venv
.\.venv\Scripts\activate          # Windows
# source .venv/bin/activate       # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run application
python app.py
```

Open **http://localhost:5000** in your browser. 🎉

---

## ⚙️ Environment Variables

Configure application settings via environment variables or `.env`:

| Variable | Default Value | Purpose |
|---|---|---|
| `SECRET_KEY` | `super-secret-dev-key` | Flask session secret key |
| `JWT_SECRET_KEY` | `jwt-dev-secret-key-change-me` | Secret key used to sign JWTs |
| `DATABASE_URL` | `sqlite:///instance/auth.db` | Database connection URI (e.g. `postgresql://user:pass@localhost/dbname`) |
| `JWT_ACCESS_MINUTES` | `30` | Access token lifespan in minutes |
| `JWT_REFRESH_DAYS` | `7` | Refresh token lifespan in days |
| `MAX_LOGIN_ATTEMPTS` | `5` | Failed attempts before lockout |
| `LOGIN_LOCKOUT_MINUTES`| `15` | Duration of brute-force lockout |

---

## 🔌 API Reference

### Auth Endpoints

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/register` | Create a new user account | ❌ No |
| `POST` | `/api/login` | Authenticate user & issue JWT cookies | ❌ No |
| `POST` | `/api/refresh` | Exchange refresh token for new access token | ❌ No |
| `POST` | `/api/logout` | Revoke current session & clear cookies | ✅ Yes |
| `GET`  | `/api/me` | Fetch authenticated user profile | ✅ Yes |
| `POST` | `/api/revoke-session/<id>` | Revoke a specific active session | ✅ Yes |
| `POST` | `/api/revoke-all` | Revoke all other active sessions | ✅ Yes |
| `POST` | `/api/change-password` | Update account password | ✅ Yes |

#### Sample API Response (`POST /api/login`)
```json
{
  "message": "Login successful!",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6Ik...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6Ik...",
  "user": {
    "id": 1,
    "username": "divyanshu",
    "email": "divyanshu@example.com",
    "full_name": "Divyanshu Srivastava",
    "created_at": "2026-08-25T13:00:00+00:00",
    "is_active": true
  }
}
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

<p align="center">Made with ❤️, Flask & Security Best Practices</p>
