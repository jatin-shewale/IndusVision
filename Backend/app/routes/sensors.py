"""
IndusVision Backend - Sensor Routes
======================================
This is the REAL version of what iot/test_server.py mocked. The ESP32 firmware's
BACKEND_URL should point here once this server is running: /api/sensors/ingest

Flow per reading:
  1. Store raw reading in MongoDB (sensor_readings collection)
  2. Run rule-based predictive maintenance scoring
  3. Update the machine's status/health_score
  4. If fault=true OR health score is low, create an Alert (Module 7)
"""
from datetime import datetime, timezone
import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.database import sensor_readings_collection, machines_collection, maintenance_collection
from app.core.dependencies import get_current_user
from app.models.machine import SensorReadingIn, SensorReadingOut
from app.services.predictive_maintenance import calculate_health_score
from app.services.alert_service import create_alert

router = APIRouter(prefix="/api/sensors", tags=["Sensors / IoT"])
logger = logging.getLogger(__name__)


@router.post("/ingest", status_code=201)
async def ingest_sensor_data(reading: SensorReadingIn, background_tasks: BackgroundTasks):
    """
    Public ingestion endpoint for ESP32 devices (no auth — IoT devices can't easily hold a JWT).
    In production, protect this with a device API key header instead; see note at bottom of file.
    """
    now = datetime.now(timezone.utc)
    doc = reading.model_dump()
    doc["timestamp"] = now
    result = await sensor_readings_collection.insert_one(doc)
    logger.info(
        "sensor_ingest_received id=%s machine_id=%s temperature=%s humidity=%s vibration=%s current_amps=%s gas_raw=%s distance_cm=%s fault=%s",
        result.inserted_id,
        reading.machine_id,
        reading.temperature,
        reading.humidity,
        reading.vibration,
        reading.current_amps,
        reading.gas_raw,
        reading.distance_cm,
        reading.fault,
    )

    # Run predictive maintenance scoring on this reading
    prediction = calculate_health_score(doc)

    # Keep an unknown device id from losing its latest status. The project's
    # firmware uses MACHINE_01, pre-seeded by seed_data.py.
    new_status = "fault" if reading.fault or prediction["predicted_status"] == "failure" else \
                 "maintenance" if prediction["predicted_status"] == "warning" else "running"

    await machines_collection.update_one(
        {"machine_id": reading.machine_id},
        {"$set": {
            "status": new_status,
            "health_score": prediction["health_score"],
            "last_seen": now,
        }, "$setOnInsert": {
            "name": f"Machine {reading.machine_id}",
            "machine_type": "ESP32 monitored equipment",
            "created_at": now,
        }},
        upsert=True,
    )

    # Store the maintenance prediction snapshot
    pred_doc = {
        **prediction,
        "machine_id": reading.machine_id,
        "fault_detected": bool(reading.fault or prediction["predicted_status"] == "failure"),
        **{key: doc.get(key) for key in ("temperature", "humidity", "vibration", "current_amps", "gas_raw", "distance_cm")},
    }
    await maintenance_collection.insert_one(pred_doc)

    # Trigger alert if needed
    if reading.fault or prediction["predicted_status"] in ("warning", "failure"):
        severity = "critical" if reading.fault or prediction["predicted_status"] == "failure" else "warning"
        reasons = prediction["reasons"] or ["ESP32 fault flag is set; individual cause was not identified"]
        def reading_value(value: float, unit: str = "") -> str:
            return "Unavailable" if value < 0 else f"{value:g}{unit}"

        details = "\n".join([
            "Detected issue(s):",
            *[f"- {reason}" for reason in reasons],
            "",
            "Sensor readings:",
            f"- Temperature: {reading_value(reading.temperature, ' °C')}",
            f"- Humidity: {reading_value(reading.humidity, '%')}",
            f"- Vibration: {reading.vibration} (0 = normal, 1 = vibration detected)",
            f"- Current: {reading_value(reading.current_amps, ' A')}",
            f"- Gas / smoke raw value: {reading.gas_raw}",
            f"- Distance: {reading_value(reading.distance_cm, ' cm')}",
            f"- ESP32 fault flag: {'YES' if reading.fault else 'NO'}",
            f"- Machine health score: {prediction['health_score']}/100",
        ])
        await create_alert(
            title=f"Machine {reading.machine_id} — {prediction['predicted_status'].upper()}",
            message=details,
            severity=severity,
            source="sensor",
            machine_id=reading.machine_id,
            deduplicate_open=True,
            background_tasks=background_tasks,
        )

    logger.info(
        "sensor_ingest_stored id=%s machine_id=%s health_score=%s predicted_status=%s",
        result.inserted_id,
        reading.machine_id,
        prediction["health_score"],
        prediction["predicted_status"],
    )
    return {"status": "received", "id": str(result.inserted_id), "prediction": prediction}


@router.get("/{machine_id}", response_model=list[SensorReadingOut])
async def get_sensor_history(machine_id: str, limit: int = 100, current_user: dict = Depends(get_current_user)):
    readings = await sensor_readings_collection.find({"machine_id": machine_id}) \
        .sort("timestamp", -1).limit(limit).to_list(limit)
    return [
        {**r, "id": str(r["_id"])} for r in readings
    ]


@router.get("/{machine_id}/latest", response_model=SensorReadingOut)
async def get_latest_reading(machine_id: str, current_user: dict = Depends(get_current_user)):
    reading = await sensor_readings_collection.find_one(
        {"machine_id": machine_id}, sort=[("timestamp", -1)]
    )
    if not reading:
        raise HTTPException(status_code=404, detail="No readings found for this machine")
    return {**reading, "id": str(reading["_id"])}

# NOTE ON SECURING /ingest FOR PRODUCTION:
# Add a simple device API key check instead of full JWT (ESP32 firmware would send a header,
# e.g. X-Device-Key: <per-machine secret>), validated against a `device_keys` collection.
# Left open here so you can get the hardware demo working first without cert/token complexity.
