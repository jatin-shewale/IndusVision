"""
IndusVision Backend - User Models
"""
from datetime import datetime, timezone
from typing import Optional, Literal
from pydantic import BaseModel, EmailStr, Field

Role = Literal["admin", "engineer", "supervisor", "operator"]


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str = Field(min_length=6)
    role: Role = "operator"
    department: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    name: str
    # Stored account addresses may predate strict EmailStr validation (for
    # example the seeded admin uses the internal .local domain).
    email: str
    role: Role
    department: Optional[str] = None
    is_active: bool = True
    created_at: datetime


class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[Role] = None
    department: Optional[str] = None
    is_active: Optional[bool] = None


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOut


def user_doc_to_out(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "name": doc["name"],
        "email": doc["email"],
        "role": doc["role"],
        "department": doc.get("department"),
        "is_active": doc.get("is_active", True),
        "created_at": doc.get("created_at", datetime.now(timezone.utc)),
    }
