"""
IndusVision Backend - Auth Dependencies (current user + role-based access control)
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.security import decode_token
from app.database import users_collection

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

ROLES = ["admin", "engineer", "supervisor", "operator"]


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(token)
    if payload is None or payload.get("type") != "access":
        raise credentials_error

    email = payload.get("sub")
    if email is None:
        raise credentials_error

    user = await users_collection.find_one({"email": email})
    if user is None:
        raise credentials_error
    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="User account is deactivated")

    user["_id"] = str(user["_id"])
    return user


def require_roles(*allowed_roles: str):
    """
    Dependency factory for role-based access control.
    Usage: Depends(require_roles("admin", "engineer"))
    """
    async def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user.get("role") not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {', '.join(allowed_roles)}",
            )
        return current_user
    return role_checker
