import os
from dotenv import load_dotenv

load_dotenv()

APP_PEPPER: str = os.getenv("APP_PEPPER", "")
if not APP_PEPPER:
    raise RuntimeError(
        "CRITICAL: APP_PEPPER environment variable is not set. "
        "The application cannot start without a pepper for password security."
    )

JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
if not JWT_SECRET_KEY:
    raise RuntimeError(
        "CRITICAL: JWT_SECRET_KEY environment variable is not set. "
        "The application cannot start without a JWT signing key."
    )

JWT_ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))

DATABASE_URL: str = os.getenv("DATABASE_URL", "")
if not DATABASE_URL:
    raise RuntimeError(
        "CRITICAL: DATABASE_URL environment variable is not set. "
        "Use a MySQL URL such as mysql+pymysql://user:pass@localhost:3306/secure_auth_db."
    )

if not DATABASE_URL.startswith("mysql+pymysql://"):
    raise RuntimeError(
        "CRITICAL: This project is configured to use MySQL only. "
        "Set DATABASE_URL to mysql+pymysql://user:pass@host:3306/database."
    )

COOKIE_SECURE: bool = os.getenv("COOKIE_SECURE", "false").lower() == "true"
COOKIE_SAMESITE: str = os.getenv("COOKIE_SAMESITE", "lax").lower()
REFRESH_TOKEN_EXPIRE_DAYS: int = int(
    os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

ALLOWED_ORIGINS: list[str] = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", "http://localhost:8000").split(",")
]

MAX_FAILED_ATTEMPTS: int = int(os.getenv("MAX_FAILED_ATTEMPTS", "5"))
LOCKOUT_DURATION_MINUTES: int = int(
    os.getenv("LOCKOUT_DURATION_MINUTES", "15"))
