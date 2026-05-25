from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session
from fastapi import Cookie, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.database import get_db
from app.models import RefreshSession, User
from app.schemas import RegisterRequest
from app.security import (
    generate_salt,
    hash_password,
    verify_password,
    validate_password_strength,
    create_access_token,
    generate_refresh_token,
    hash_token,
    verify_access_token,
    sanitize_input,
)
from app.config import (
    MAX_FAILED_ATTEMPTS,
    LOCKOUT_DURATION_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
)

security_scheme = HTTPBearer(auto_error=False)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def register_user(request: RegisterRequest, db: Session) -> dict:

    username = sanitize_input(request.username)

    strength_result = validate_password_strength(request.password)
    if not strength_result["valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password too weak: {'; '.join(strength_result['errors'])}",
        )

    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )

    salt = generate_salt()

    password_hash = hash_password(request.password, salt)

    new_user = User(
        username=username,
        password_hash=password_hash,
        salt=salt,
        failed_attempts=0,
        locked_until=None,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "Registration successful. Please log in."}


def authenticate_user(username: str, password: str, db: Session) -> dict:

    username = sanitize_input(username)

    user = db.query(User).filter(User.username == username).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    if user.locked_until:
        now = _utc_now()
        if _as_utc(user.locked_until) > now:
            remaining = (_as_utc(user.locked_until) - now).seconds // 60
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account locked. Try again in {remaining + 1} minute(s).",
            )
        user.failed_attempts = 0
        user.locked_until = None
        db.commit()

    if not verify_password(password, user.salt, user.password_hash):
        user.failed_attempts += 1

        if user.failed_attempts >= MAX_FAILED_ATTEMPTS:
            user.locked_until = _utc_now() + timedelta(
                minutes=LOCKOUT_DURATION_MINUTES
            )
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account locked due to {MAX_FAILED_ATTEMPTS} failed attempts. "
                f"Try again in {LOCKOUT_DURATION_MINUTES} minutes.",
            )

        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    user.failed_attempts = 0
    user.locked_until = None
    db.commit()

    access_token = create_access_token(data={"sub": user.username})
    refresh_token = generate_refresh_token()
    refresh_session = RefreshSession(
        user_id=user.id,
        token_hash=hash_token(refresh_token),
        expires_at=_utc_now() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(refresh_session)
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "message": "Login successful",
    }


def refresh_user_session(refresh_token: str | None, db: Session) -> dict:
    """Rotate a valid refresh token and return a new access token pair."""
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing refresh token",
        )

    session = (
        db.query(RefreshSession)
        .filter(RefreshSession.token_hash == hash_token(refresh_token))
        .first()
    )
    now = _utc_now()
    if not session or session.revoked or _as_utc(session.expires_at) <= now:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user = db.query(User).filter(User.id == session.user_id).first()
    if not user:
        session.revoked = True
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session",
        )

    session.revoked = True
    new_refresh_token = generate_refresh_token()
    new_session = RefreshSession(
        user_id=user.id,
        token_hash=hash_token(new_refresh_token),
        expires_at=now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        last_used_at=now,
    )
    db.add(new_session)
    db.commit()

    return {
        "access_token": create_access_token(data={"sub": user.username}),
        "refresh_token": new_refresh_token,
        "message": "Session refreshed",
    }


def revoke_refresh_session(refresh_token: str | None, db: Session) -> None:
    """Revoke the current refresh session if it exists."""
    if not refresh_token:
        return
    session = (
        db.query(RefreshSession)
        .filter(RefreshSession.token_hash == hash_token(refresh_token))
        .first()
    )
    if session:
        session.revoked = True
        db.commit()


def get_current_user(
    access_token: str | None = Cookie(default=None),
    credentials: HTTPAuthorizationCredentials | None = Depends(
        security_scheme),
    db: Session = Depends(get_db),
) -> User:

    token = access_token or (credentials.credentials if credentials else None)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = verify_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Fetch user from database
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user
