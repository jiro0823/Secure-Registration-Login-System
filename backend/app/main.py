import os
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import ALLOWED_ORIGINS
from app.routes.auth_routes import router as auth_router, limiter


logger = logging.getLogger("secure_auth")


app = FastAPI(
    title="Secure Registration & Login System",
    description=(
        "A production-grade authentication system demonstrating "
        "OWASP Top 10 compliance, bcrypt + salt + pepper password hashing, "
        "JWT authentication, rate limiting, and account lockout."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """
    Add security headers to all HTTP responses.

    These headers protect against:
    - Clickjacking (X-Frame-Options)
    - MIME-type sniffing (X-Content-Type-Options)
    - XSS attacks (Content-Security-Policy, X-XSS-Protection)
    - Information leakage (Referrer-Policy)
    - Downgrade attacks (Strict-Transport-Security)
    """
    response = await call_next(request)

    response.headers["X-Frame-Options"] = "DENY"

    response.headers["X-Content-Type-Options"] = "nosniff"

    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "base-uri 'self'; "
        "form-action 'self'; "
        "frame-ancestors 'none'; "
        "object-src 'none'; "
        "script-src 'self'; "
        "style-src 'self' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data:; "
        "connect-src 'self'"
    )

    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    response.headers["X-XSS-Protection"] = "1; mode=block"

    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )

    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    response.headers["Cross-Origin-Resource-Policy"] = "cross-origin"

    return response

app.include_router(auth_router, prefix="/api")

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
frontend_path = os.path.join(repo_root, "frontend")

if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")


def _read_html(filename: str) -> str:
    """Read an HTML file from the frontend directory."""
    filepath = os.path.join(frontend_path, filename)
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Page Not Found</h1>"


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def serve_login():
    """Serve the login page as the default landing page."""
    return HTMLResponse(content=_read_html("login.html"))


@app.get("/register", response_class=HTMLResponse, include_in_schema=False)
def serve_register():
    """Serve the registration page."""
    return HTMLResponse(content=_read_html("register.html"))


@app.get("/login", response_class=HTMLResponse, include_in_schema=False)
def serve_login_page():
    """Serve the login page."""
    return HTMLResponse(content=_read_html("login.html"))


@app.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
def serve_dashboard():
    """Serve the dashboard page."""
    return HTMLResponse(content=_read_html("dashboard.html"))


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catch-all exception handler.
    Security: Returns a generic error message to prevent
    information leakage through stack traces or internal errors.
    """
    logger.exception("Unhandled exception", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. Please try again later."},
    )
