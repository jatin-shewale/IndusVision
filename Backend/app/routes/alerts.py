"""
IndusVision Backend - Alert Routes (Module 7)
"""
from datetime import datetime, timezone
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException, Depends

from app.database import alerts_collection
from app.core.dependencies import get_current_user, require_roles
from app.models.alert import AlertCreate, AlertOut

router = APIRouter(prefix="/api/alerts", tags=["Alerts"])


def _alert_out(doc: dict) -> dict:
    return {**{k: v for k, v in doc.items() if k != "_id"}, "id": str(doc["_id"])}


@router.post("", response_model=AlertOut, status_code=201)
async def create_manual_alert(alert: AlertCreate, current_user: dict = Depends(require_roles("admin", "engineer", "supervisor"))):
    doc = alert.model_dump()
    doc["status"] = "open"
    doc["created_at"] = datetime.now(timezone.utc)
    result = await alerts_collection.insert_one(doc)
    doc["_id"] = result.inserted_id
    return _alert_out(doc)


@router.get("", response_model=list[AlertOut])
async def list_alerts(status: str | None = None, severity: str | None = None, limit: int = 200,
                       current_user: dict = Depends(get_current_user)):
    query = {}
    if status:
        query["status"] = status
    if severity:
        query["severity"] = severity
    docs = await alerts_collection.find(query).sort("created_at", -1).limit(limit).to_list(limit)
    return [_alert_out(d) for d in docs]


@router.patch("/{alert_id}/acknowledge", response_model=AlertOut)
async def acknowledge_alert(alert_id: str, current_user: dict = Depends(get_current_user)):
    try:
        oid = ObjectId(alert_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid alert id")
    doc = await alerts_collection.find_one_and_update(
        {"_id": oid}, {"$set": {"status": "acknowledged"}}, return_document=True
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Alert not found")
    return _alert_out(doc)


@router.patch("/{alert_id}/resolve", response_model=AlertOut)
async def resolve_alert(alert_id: str, current_user: dict = Depends(require_roles("admin", "engineer", "supervisor"))):
    try:
        oid = ObjectId(alert_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid alert id")
    doc = await alerts_collection.find_one_and_update(
        {"_id": oid}, {"$set": {"status": "resolved"}}, return_document=True
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Alert not found")
    return _alert_out(doc)
