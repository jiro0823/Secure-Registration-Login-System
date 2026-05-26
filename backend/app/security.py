import re
import html
import logging
import secrets
import hashlib
from datetime import datetime, timedelta, timezone

from passlib.context import CryptContext
from jose import jwt, JWTError

from app.config import (
    APP_PEPPER,
    JWT_SECRET_KEY,
    JWT_ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

# ---------------------------------------------------------------------------
# Suppress passlib bcrypt version warning
# passlib 1.7.4 checks for bcrypt.__about__.__version__ which was removed
# in newer bcrypt versions. This silences the false warning.
# ---------------------------------------------------------------------------
logging.getLogger("passlib").setLevel(logging.ERROR)

# ---------------------------------------------------------------------------
# Password Hash Configuration
# Use bcrypt with a pre-hash step to avoid the 72-byte bcrypt limit.
# deprecated="auto" ensures old hashes are automatically rehashed
# ---------------------------------------------------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ===========================================================================
# SALT GENERATION
# ===========================================================================

def generate_salt() -> str:
    """
    Generate a unique cryptographically secure salt for each user.

    Security: Each user gets a unique salt, so even if two users have
    the same password, their hashes will be completely different.
    This prevents rainbow table and precomputation attacks.

    Returns:
        64-character hex string (32 bytes of randomness)
    """
    return secrets.token_hex(32)


def generate_refresh_token() -> str:
    """Generate a high-entropy refresh token for cookie storage."""
    return secrets.token_urlsafe(64)


def hash_token(token: str) -> str:
    """Hash a bearer token before storing it in the database."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# ===========================================================================
# PASSWORD HASHING (Salt + Pepper + Bcrypt)
# ===========================================================================

def _prehash_password(password: str, salt: str) -> str:
    """Pre-hash password+salt+pepper to a fixed length for bcrypt."""
    combined = (password + salt + APP_PEPPER).encode("utf-8")
    return hashlib.sha256(combined).hexdigest()


def hash_password(password: str, salt: str) -> str:
    """
    Hash a password using bcrypt with salt and pepper.

    Formula: bcrypt(password + salt + pepper)

    Security:
    - Salt (unique per user) prevents rainbow table attacks
    - Pepper (from .env, never in DB) adds defense-in-depth
    - Even if the database is fully compromised, the attacker still
      needs the pepper to attempt offline cracking
    - Bcrypt's adaptive work factor makes brute force infeasible

    Args:
        password: Plaintext password from user input
        salt: Unique salt generated for this user

    Returns:
        Bcrypt hash string
    """
    # Pre-hash to avoid bcrypt 72-byte limit, then bcrypt the fixed-length digest
    prehashed = _prehash_password(password, salt)
    return pwd_context.hash(prehashed)


def verify_password(password: str, salt: str, stored_hash: str) -> bool:
    """
    Verify a password against the stored bcrypt hash.

    Recomputes: bcrypt.verify(password + salt + pepper, stored_hash)

    Security:
    - Uses constant-time comparison internally (bcrypt handles this)
    - Prevents timing attacks on password verification

    Args:
        password: Plaintext password from login attempt
        salt: User's stored salt from database
        stored_hash: User's stored bcrypt hash from database

    Returns:
        True if password is correct, False otherwise
    """
    prehashed = _prehash_password(password, salt)
    return pwd_context.verify(prehashed, stored_hash)


# ===========================================================================
# PASSWORD STRENGTH VALIDATION
# ===========================================================================

def validate_password_strength(password: str) -> dict:
    """
    Validate password strength against security requirements.

    Rules:
    - Minimum 12 characters
    - At least 1 uppercase letter
    - At least 1 lowercase letter
    - At least 1 digit
    - At least 1 special symbol (!@#$%^&*()_+-=[]{}|;:',.<>?/~`)

    Security: Server-side validation is mandatory because client-side
    validation can be bypassed. This is the authoritative check.

    Args:
        password: Password to validate

    Returns:
        dict with 'valid' (bool), 'strength' (str), 'errors' (list),
        and 'checks' (dict of individual rule results)
    """
    checks = {
        "min_length": len(password) >= 12,
        "uppercase": bool(re.search(r"[A-Z]", password)),
        "lowercase": bool(re.search(r"[a-z]", password)),
        "digit": bool(re.search(r"\d", password)),
        "special": bool(re.search(r"[!@#$%^&*()_+\-=\[\]{}|;:'\",.<>?/~`\\]", password)),
    }

    errors = []
    if not checks["min_length"]:
        errors.append("Password must be at least 12 characters long")
    if not checks["uppercase"]:
        errors.append("Password must contain at least 1 uppercase letter")
    if not checks["lowercase"]:
        errors.append("Password must contain at least 1 lowercase letter")
    if not checks["digit"]:
        errors.append("Password must contain at least 1 digit")
    if not checks["special"]:
        errors.append("Password must contain at least 1 special character")

    # Calculate strength level
    passed = sum(checks.values())
    if passed <= 2:
        strength = "Weak"
    elif passed <= 4:
        strength = "Medium"
    else:
        strength = "Strong"

    return {
        "valid": all(checks.values()),
        "strength": strength,
        "errors": errors,
        "checks": checks,
    }


# ===========================================================================
# JWT TOKEN MANAGEMENT
# ===========================================================================

def create_access_token(data: dict) -> str:
    """
    Create a JWT access token with expiration.

    Security:
    - Short expiry (15 minutes) limits the window of token theft
    - HS256 signing prevents token tampering
    - Secret key from .env, never hardcoded

    Args:
        data: Payload to encode (typically {"sub": username})

    Returns:
        Encoded JWT string
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + \
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY,
                             algorithm=JWT_ALGORITHM)
    return encoded_jwt


def verify_access_token(token: str) -> dict | None:
    """
    Verify and decode a JWT access token.

    Security:
    - Validates signature to ensure token hasn't been tampered with
    - Checks expiration automatically (jose handles this)
    - Returns None on any failure — never leaks error details

    Args:
        token: JWT string from the HttpOnly access cookie or API docs bearer header

    Returns:
        Decoded payload dict if valid, None if invalid/expired
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


# ===========================================================================
# INPUT SANITIZATION
# ===========================================================================

def sanitize_input(value: str) -> str:
    """
    Sanitize user input to prevent XSS and injection attacks.

    Security:
    - HTML-encodes special characters (<, >, &, ", ')
    - Strips leading/trailing whitespace
    - Prevents stored XSS when rendering user data

    Args:
        value: Raw user input string

    Returns:
        Sanitized string safe for storage and display
    """
    if not isinstance(value, str):
        return ""
    # Strip whitespace
    value = value.strip()
    # HTML-encode to prevent XSS
    value = html.escape(value)
    return value
