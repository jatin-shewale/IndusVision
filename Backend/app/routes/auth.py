"""
IndusVision Backend - Auth Routes
Module 1: Authentication (Admin/Engineer/Supervisor/Operator login, JWT, refresh, RBAC)
"""
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.database import users_collection
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.core.dependencies import get_current_user, require_roles
from app.models.user import UserCreate, UserOut, Token, user_doc_to_out

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=UserOut, status_code=201)
async def register(user_in: UserCreate, current_user: dict = Depends(require_roles("admin"))):
    """Only admins can create new users (per the project's role-based access spec)."""
    existing = await users_collection.find_one({"email": user_in.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    doc = {
        "name": user_in.name,
        "email": user_in.email,
        "password_hash": hash_password(user_in.password),
        "role": user_in.role,
        "department": user_in.department,
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
    }
    result = await users_collection.insert_one(doc)
    doc["_id"] = result.inserted_id
    return user_doc_to_out(doc)


@router.post("/bootstrap-admin", response_model=UserOut, status_code=201)
async def bootstrap_admin(user_in: UserCreate):
    """
    One-time-use endpoint to create the FIRST admin account when the database is empty.
    Refuses if any user already exists — use /register (admin-only) after that.
    """
    if await users_collection.count_documents({}) > 0:
        raise HTTPException(status_code=403, detail="Admin already exists. Use /api/auth/register instead.")

    doc = {
        "name": user_in.name,
        "email": user_in.email,
        "password_hash": hash_password(user_in.password),
        "role": "admin",
        "department": user_in.department,
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
    }
    result = await users_collection.insert_one(doc)
    doc["_id"] = result.inserted_id
    return user_doc_to_out(doc)


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """OAuth2-compatible login: send as form data (username=email, password=password)."""
    user = await users_collection.find_one({"email": form_data.username})
    if not user or not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="Account is deactivated")

    access_token = create_access_token({"sub": user["email"], "role": user["role"]})
    refresh_token = create_refresh_token({"sub": user["email"]})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user_doc_to_out(user),
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str):
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user = await users_collection.find_one({"email": payload["sub"]})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    new_access = create_access_token({"sub": user["email"], "role": user["role"]})
    new_refresh = create_refresh_token({"sub": user["email"]})
    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
        "user": user_doc_to_out(user),
    }


@router.get("/me", response_model=UserOut)
async def get_me(current_user: dict = Depends(get_current_user)):
    return user_doc_to_out(current_user)
