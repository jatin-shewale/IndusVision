"""
IndusVision Backend - Machine Routes
"""
from datetime import datetime, timezone
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException, Depends

from app.database import machines_collection
from app.core.dependencies import get_current_user, require_roles
from app.models.machine import MachineCreate, MachineOut

router = APIRouter(prefix="/api/machines", tags=["Machines"])


def _machine_out(doc: dict) -> dict:
    return {
        "id": str(doc["_id"]),
        "machine_id": doc["machine_id"],
        "name": doc["name"],
        "location": doc.get("location"),
        "machine_type": doc.get("machine_type"),
        "status": doc.get("status", "offline"),
        "health_score": doc.get("health_score"),
        "last_seen": doc.get("last_seen"),
    }


@router.post("", response_model=MachineOut, status_code=201)
async def create_machine(machine: MachineCreate, current_user: dict = Depends(require_roles("admin", "engineer"))):
    existing = await machines_collection.find_one({"machine_id": machine.machine_id})
    if existing:
        raise HTTPException(status_code=400, detail="Machine ID already exists")

    doc = machine.model_dump()
    doc["status"] = "offline"
    doc["health_score"] = None
    doc["last_seen"] = None
    doc["created_at"] = datetime.now(timezone.utc)
    result = await machines_collection.insert_one(doc)
    doc["_id"] = result.inserted_id
    return _machine_out(doc)


@router.get("", response_model=list[MachineOut])
async def list_machines(current_user: dict = Depends(get_current_user)):
    machines = await machines_collection.find().to_list(500)
    return [_machine_out(m) for m in machines]


@router.get("/{machine_id}", response_model=MachineOut)
async def get_machine(machine_id: str, current_user: dict = Depends(get_current_user)):
    doc = await machines_collection.find_one({"machine_id": machine_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Machine not found")
    return _machine_out(doc)


@router.delete("/{machine_id}", status_code=204)
async def delete_machine(machine_id: str, current_user: dict = Depends(require_roles("admin"))):
    result = await machines_collection.delete_one({"machine_id": machine_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Machine not found")
