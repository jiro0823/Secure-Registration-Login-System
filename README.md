# 🔐 Secure Registration & Login System

> A production-grade authentication system demonstrating OWASP Top 10 compliance, secure password handling, and cybersecurity best practices.

![Python](https://img.shields.io/badge/Python-3.13+-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green?style=flat-square&logo=fastapi)
![Security](https://img.shields.io/badge/Security-OWASP%20Top%2010-red?style=flat-square&logo=owasp)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

---

## 🎯 Features

### Core Authentication

- ✅ **Secure Registration** with input validation and sanitization
- ✅ **Secure Login** with generic error messages (prevents user enumeration)
- ✅ **Password Strength Meter** with real-time animated feedback
- ✅ **HttpOnly Cookie Authentication** with 15-minute JWT access cookies

### Password Security

- 🔐 **Bcrypt Hashing** — adaptive, GPU-resistant algorithm
- 🧂 **Unique Salt Per User** — prevents rainbow table attacks
- 🌶️ **Secret Pepper** — stored only in environment variables
- 📏 **Strength Validation** — 12+ chars, uppercase, lowercase, digit, special

### Advanced Security

- 🛡️ **Rate Limiting** — 5 login attempts per minute (SlowAPI)
- 🔒 **Account Lockout** — 15-minute lock after 5 failed attempts
- 📋 **Security Headers** — CSP, X-Frame-Options, HSTS, Referrer-Policy
- 🌐 **CORS Whitelist** — strict origin control
- 🧹 **Input Sanitization** — XSS and injection prevention
- 💉 **SQL Injection Prevention** — SQLAlchemy ORM only
- 🍪 **HttpOnly Cookies** — JWTs are not exposed to browser JavaScript
- 🗄️ **PostgreSQL/Supabase Session Defense** — refresh tokens are hashed, stored, rotated, and revocable

### Frontend

- 🎨 **Cybersecurity-Themed UI** — dark mode, glowing effects, animations
- 📱 **Responsive Design** — mobile-friendly
- ⚡ **Real-time Validation** — instant password strength feedback

---

## 🛠️ Tech Stack

| Layer             | Technology                            |
| ----------------- | ------------------------------------- |
| **Backend**       | Python 3.13+, FastAPI, Uvicorn        |
| **ORM**           | SQLAlchemy                            |
| **Validation**    | Pydantic                              |
| **Hashing**       | Passlib (bcrypt)                      |
| **JWT**           | python-jose                           |
| **Rate Limiting** | SlowAPI                               |
| **Database**      | PostgreSQL/Supabase (via SQLAlchemy)  |
| **Frontend**      | HTML5, Custom CSS, Vanilla JavaScript |
| **Deployment**    | Render                                |

---

## 📁 Project Structure

```
secure_auth_system/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py          # FastAPI app + middleware
│   │   ├── config.py         # Environment configuration
│   │   ├── database.py       # SQLAlchemy setup
│   │   ├── models.py         # User ORM model
│   │   ├── schemas.py        # Pydantic validation
│   │   ├── security.py       # Hashing, JWT, sanitization
│   │   ├── auth.py           # Auth business logic
│   │   └── routes/
│   │       ├── __init__.py
│   │       └── auth_routes.py # API endpoints
│   ├── requirements.txt
│   ├── .env                   # Secrets (not committed)
│   └── Procfile               # Deployment command
├── frontend/
│   ├── register.html
│   ├── login.html
│   ├── dashboard.html
│   ├── css/styles.css
│   └── js/
│       ├── auth.js
│       └── password-strength.js
├── documentation/
│   └── SECURITY.md
├── screenshots/
├── .gitignore
├── render.yaml
└── README.md
```

---

## 🚀 Quick Start (Local)

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd Secure-Registration&Login-System
```

### 2. Create virtual environment

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

The `.env` file is pre-configured for local development. For production, update:

- `APP_PEPPER` — change to a unique secret
- `JWT_SECRET_KEY` — generate new: `python -c "import secrets; print(secrets.token_hex(32))"`
- `ALLOWED_ORIGINS` — add your production URL
- `DATABASE_URL` — set your Supabase PostgreSQL connection string
- `COOKIE_SECURE` — use `false` for local HTTP, `true` for production HTTPS

For production, use a hosted PostgreSQL database such as Supabase. Local XAMPP
MySQL is not reachable from Render.

### 5. Run the server

```powershell
.\run-local.cmd
```

The local runner uses port `8000` when available. If something is already
listening there, it automatically tries the next free port.

### 6. Open in browser

- **Login**: http://localhost:8000
- **Register**: http://localhost:8000/register
- **Dashboard**: http://localhost:8000/dashboard
- **API Docs**: http://localhost:8000/docs

---

## 📡 API Endpoints

| Method | Endpoint        | Description             | Auth |
| ------ | --------------- | ----------------------- | ---- |
| `POST` | `/api/register` | Register new user       | ❌   |
| `POST` | `/api/login`    | Authenticate + set HttpOnly cookies | ❌   |
| `POST` | `/api/refresh`  | Rotate refresh session  | ❌   |
| `POST` | `/api/logout`   | Revoke session + clear cookies | ✅   |
| `GET`  | `/api/me`       | Get user profile        | ✅   |
| `GET`  | `/api/health`   | Health check            | ❌   |

---

## ☁️ Deploy to Render

### Step-by-step:

1. **Push to GitHub** (ensure `.env` is in `.gitignore`)
2. **Create Render account** at [render.com](https://render.com)
3. **New Web Service** → Connect your GitHub repo
4. **Configure**:
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. **Environment Variables** (add in Render dashboard):
   - `APP_PEPPER` = your secret pepper
   - `JWT_SECRET_KEY` = your JWT secret
   - `ALLOWED_ORIGINS` = `https://your-app.onrender.com`
   - `DATABASE_URL` = `postgresql://user:pass@host:5432/postgres`
   - `COOKIE_SECURE` = `true`
   - `COOKIE_SAMESITE` = `lax`
6. **Deploy** → Get your public URL

---

## 📸 Screenshots

> Add screenshots to the `/screenshots` directory after testing.

---

## 📄 License

This project is created for educational purposes as a Cybersecurity Final Project.
