"""
auth_routes.py — API Route Definitions
=========================================
Security Rationale:
- Rate limiting on /login prevents brute force attacks (5 req/min)
- All routes return generic error messages
- Protected routes require a valid HttpOnly access cookie via get_current_user
- No sensitive data ever appears in response bodies
- Input validation handled by Pydantic schemas before reaching handlers

API Routes:
    POST /register  — Create new user account
    POST /login     — Authenticate and receive JWT
    POST /logout    — Client-side token invalidation guidance
    GET  /me        — Get current user profile (JWT required)
    GET  /health    — Health check endpoint
"""

from fastapi import APIRouter, Cookie, Depends, Request, Response
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.database import get_db
from app.models import User
from app.schemas import (
    RegisterRequest,
    LoginRequest,
    UserResponse,
    MessageResponse,
)
from app.auth import (
    register_user,
    authenticate_user,
    get_current_user,
    refresh_user_session,
    revoke_refresh_session,
)
from app.config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    COOKIE_SAMESITE,
    COOKIE_SECURE,
    REFRESH_TOKEN_EXPIRE_DAYS,
)

# ---------------------------------------------------------------------------
# Rate Limiter Instance
# Security: Limits request frequency to prevent brute force attacks
# ---------------------------------------------------------------------------
limiter = Limiter(key_func=get_remote_address)

# ---------------------------------------------------------------------------
# Router Instance
# ---------------------------------------------------------------------------
router = APIRouter(tags=["Authentication"])


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        path="/api",
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/api")


# ===========================================================================
# POST /register — User Registration
# ===========================================================================
@router.post(
    "/register",
    response_model=MessageResponse,
    status_code=201,
    summary="Register a new user",
    description="Create a new user account with secure password hashing (salt + pepper + bcrypt).",
)
@limiter.limit("5/minute")
def register(request: Request, register_data: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user.

    Security flow:
    1. Pydantic validates input (length, format, password match)
    2. Server-side password strength check
    3. Username uniqueness check
    4. Generate salt → hash(password + salt + pepper) → store
    """
    result = register_user(register_data, db)
    return result


# ===========================================================================
# POST /login — User Authentication
# ===========================================================================
@router.post(
    "/login",
    response_model=MessageResponse,
    summary="Authenticate user",
    description="Verify credentials and set HttpOnly authentication cookies. Rate limited to 5 attempts per minute.",
)
@limiter.limit("5/minute")
def login(
    request: Request,
    response: Response,
    login_data: LoginRequest,
    db: Session = Depends(get_db),
):
    """
    Authenticate user and set HttpOnly cookies.

    Security flow:
    1. Rate limiting: max 5 attempts per minute per IP
    2. Sanitize input
    3. Fetch user + check lockout
    4. Verify: bcrypt(password + salt + pepper) == stored_hash
    5. On failure: increment counter, lock after 5 fails
    6. On success: reset counter, set short-lived access cookie and
       DB-backed refresh cookie
    """
    result = authenticate_user(login_data.username, login_data.password, db)
    _set_auth_cookies(response, result["access_token"], result["refresh_token"])
    return {"message": result["message"]}


@router.post(
    "/refresh",
    response_model=MessageResponse,
    summary="Refresh session",
    description="Rotate the MySQL-backed refresh token and issue a new access cookie.",
)
def refresh(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
):
    result = refresh_user_session(refresh_token, db)
    _set_auth_cookies(response, result["access_token"], result["refresh_token"])
    return {"message": result["message"]}


# ===========================================================================
# POST /logout — Token Invalidation
# ===========================================================================
@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout user",
    description="Revoke the MySQL-backed refresh session and clear auth cookies.",
)
def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Logout the current user.

    Security:
    - Revokes the refresh session stored in MySQL
    - Clears HttpOnly auth cookies in the browser
    - Short-lived access cookie naturally expires quickly
    """
    revoke_refresh_session(refresh_token, db)
    _clear_auth_cookies(response)
    return {"message": "Logged out successfully."}


# ===========================================================================
# GET /me — Current User Profile
# ===========================================================================
@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Returns the authenticated user's profile. Requires valid auth cookie.",
)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Return the current authenticated user's profile.

    Security:
    - Requires valid HttpOnly access cookie
    - Only returns safe fields (id, username, created_at)
    - Never exposes password_hash, salt, or internal fields
    """
    return current_user


# ===========================================================================
# GET /health — Health Check
# ===========================================================================
@router.get(
    "/health",
    response_model=MessageResponse,
    summary="Health check",
    description="Returns server health status. No authentication required.",
)
def health_check():
    """
    Simple health check endpoint for monitoring and deployment verification.
    """
    return {"message": "Server is running securely."}
