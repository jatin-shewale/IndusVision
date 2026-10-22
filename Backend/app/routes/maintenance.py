"""IndusVision Backend - Maintenance Routes (Module 5: Predictive Maintenance)."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException

from app.database import maintenance_collection, detections_collection
from app.core.dependencies import get_current_user
from app.models.alert import MaintenancePredictionOut, MaintenanceEventOut

router = APIRouter(prefix="/api/maintenance", tags=["Predictive Maintenance"])


@router.get("/{machine_id}/latest", response_model=MaintenancePredictionOut)
async def get_latest_prediction(machine_id: str, current_user: dict = Depends(get_current_user)):
    doc = await maintenance_collection.find_one(
        {"machine_id": machine_id}, sort=[("generated_at", -1)]
    )
    if not doc:
        raise HTTPException(status_code=404, detail="No predictions yet for this machine")
    return {**doc, "id": str(doc["_id"])}


@router.get("/{machine_id}/history", response_model=list[MaintenancePredictionOut])
async def get_prediction_history(machine_id: str, limit: int = 100, current_user: dict = Depends(get_current_user)):
    docs = await maintenance_collection.find({"machine_id": machine_id}) \
        .sort("generated_at", -1).limit(limit).to_list(limit)
    return [{**d, "id": str(d["_id"])} for d in docs]


@router.get("/events", response_model=list[MaintenanceEventOut])
async def get_fault_and_safety_events(limit: int = 100, current_user: dict = Depends(get_current_user)):
    """Return persisted sensor faults/warnings and every logged PPE violation."""
    limit = max(1, min(limit, 500))
    sensor_docs = await maintenance_collection.find({
        "$or": [{"fault_detected": True}, {"predicted_status": {"$in": ["warning", "failure"]}}]
    }).sort("generated_at", -1).limit(limit).to_list(limit)
    safety_docs = await detections_collection.find({"is_violation": True}) \
        .sort("timestamp", -1).limit(limit).to_list(limit)

    events = []
    for doc in sensor_docs:
        causes = doc.get("reasons") or ["Sensor fault reported; cause unavailable in this historical record"]
        events.append({
            "id": str(doc["_id"]), "source": "sensor", "machine_id": doc.get("machine_id"),
            "title": f"Machine {doc.get('machine_id', '')} sensor event", "status": doc.get("predicted_status", "failure"),
            "causes": causes, "timestamp": doc.get("generated_at"),
            **{key: doc.get(key) for key in ("temperature", "humidity", "vibration", "current_amps", "gas_raw", "distance_cm")},
        })
    for doc in safety_docs:
        violations = sorted({item.get("class_name", "PPE violation") for item in doc.get("detections", [])
                             if item.get("class_name") in {"NO-Hardhat", "NO-Mask", "NO-Safety Vest"}})
        events.append({
            "id": str(doc["_id"]), "source": "worker_safety", "machine_id": doc.get("machine_zone"),
            "camera_id": doc.get("camera_id"), "title": f"PPE violation — {doc.get('camera_id', 'camera')}",
            "status": "failure", "causes": violations or ["PPE violation"], "timestamp": doc.get("timestamp"),
        })
    events.sort(key=lambda event: event["timestamp"] or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    return events[:limit]
