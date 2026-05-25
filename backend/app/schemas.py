from datetime import datetime

from pydantic import BaseModel, Field, field_validator
import re
import html


class RegisterRequest(BaseModel):
    
    username: str = Field(
        ...,
        min_length=3,
        max_length=30,
        description="Username must be 3-30 characters, alphanumeric and underscores only",
    )
    password: str = Field(
        ...,
        min_length=12,
        max_length=128,
        description="Password must be 12-128 characters",
    )
    confirm_password: str = Field(
        ...,
        min_length=12,
        max_length=128,
        description="Must match password field",
    )

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:

        v = v.strip()
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError(
                "Username must contain only letters, numbers, and underscores"
            )
        # HTML-encode to prevent XSS if username is ever rendered
        v = html.escape(v)
        return v

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v


class LoginRequest(BaseModel):
    """
    Login request schema.
    Minimal validation — detailed checks happen in auth logic.
    """
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=128)

    @field_validator("username")
    @classmethod
    def sanitize_username(cls, v: str) -> str:
        """Strip whitespace and HTML-encode to prevent injection."""
        return html.escape(v.strip())


class UserResponse(BaseModel):
    """
    User profile response.
    Security: Never includes password_hash, salt, or any sensitive fields.
    """
    id: int
    username: str
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    """Generic message response for success/error communication."""
    message: str
