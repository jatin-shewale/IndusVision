"""
IndusVision Backend - User Management Routes (admin only)
"""
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException, Depends

from app.database import users_collection
from app.core.dependencies import require_roles
from app.models.user import UserOut, UserUpdate, user_doc_to_out

router = APIRouter(prefix="/api/users", tags=["Users"])


@router.get("", response_model=list[UserOut])
async def list_users(current_user: dict = Depends(require_roles("admin"))):
    users = await users_collection.find().to_list(500)
    return [user_doc_to_out(u) for u in users]


@router.patch("/{user_id}", response_model=UserOut)
async def update_user(user_id: str, update: UserUpdate, current_user: dict = Depends(require_roles("admin"))):
    try:
        oid = ObjectId(user_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid user id")

    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = await users_collection.find_one_and_update(
        {"_id": oid}, {"$set": update_data}, return_document=True
    )
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    return user_doc_to_out(result)


@router.delete("/{user_id}", status_code=204)
async def delete_user(user_id: str, current_user: dict = Depends(require_roles("admin"))):
    try:
        oid = ObjectId(user_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid user id")

    result = await users_collection.delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
