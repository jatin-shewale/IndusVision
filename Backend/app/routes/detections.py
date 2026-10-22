"""Worker-Safety inference and detection log routes."""
import base64
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from starlette.concurrency import run_in_threadpool

from app.config import settings
from app.database import detections_collection
from app.core.dependencies import get_current_user
from app.models.detection import DetectionIn, DetectionOut, VIOLATION_CLASSES
from app.services.alert_service import create_alert
from app.services.ppe_inference import infer_image

router = APIRouter(prefix="/api/detections", tags=["Detections / AI"])
logger = logging.getLogger(__name__)


async def _save_detection(detection: DetectionIn, background_tasks: BackgroundTasks | None = None) -> dict:
    now = datetime.now(timezone.utc)
    class_names = {d.class_name for d in detection.detections}
    is_violation = bool(class_names & VIOLATION_CLASSES)
    doc = detection.model_dump()
    doc["timestamp"] = now
    doc["is_violation"] = is_violation
    result = await detections_collection.insert_one(doc)
    logger.info(
        "detection_stored id=%s camera_id=%s violation=%s classes=%s",
        result.inserted_id,
        detection.camera_id,
        is_violation,
        ",".join(sorted(class_names)),
    )

    if is_violation:
        violations = sorted(
            (item for item in detection.detections if item.class_name in VIOLATION_CLASSES),
            key=lambda item: item.class_name,
        )
        violated = "\n".join(
            f"- {item.class_name} (confidence: {item.confidence:.0%})" for item in violations
        )
        zone = detection.machine_zone or "Not specified"
        await create_alert(
            title=f"PPE Violation — {detection.camera_id}",
            message="\n".join([
                "Detected PPE violation(s):",
                violated,
                "",
                f"Camera: {detection.camera_id}",
                f"Machine / Zone: {zone}",
            ]),
            severity="critical",
            source="detection",
            machine_id=detection.machine_zone,
            deduplicate_open=True,
            background_tasks=background_tasks,
        )
    return {"status": "logged", "id": str(result.inserted_id), "is_violation": is_violation}


@router.post("/infer", status_code=201)
async def infer_uploaded_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    camera_id: str = Form("UPLOAD"),
    machine_zone: str | None = Form(None),
    _current_user: dict = Depends(get_current_user),
):
    """Infer an uploaded image with Worker-Safety/best.pt, then log results and alerts."""
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=415, detail="Upload an image file")
    image_bytes = await file.read(15 * 1024 * 1024 + 1)
    if len(image_bytes) > 15 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Image must be 15 MB or smaller")
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded image is empty")

    try:
        detections, annotated = await run_in_threadpool(
            infer_image, image_bytes, settings.PPE_CONFIDENCE_THRESHOLD
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PPE inference failed: {exc}") from exc

    detection = DetectionIn(
        camera_id=camera_id,
        machine_zone=machine_zone,
        detections=detections,
    )
    saved = await _save_detection(detection, background_tasks)
    return {
        **saved,
        "camera_id": camera_id,
        "machine_zone": machine_zone,
        "detections": detections,
        "annotated_image": base64.b64encode(annotated).decode("ascii"),
    }


@router.post("", status_code=201)
async def log_detection(detection: DetectionIn, background_tasks: BackgroundTasks):
    """Called by Backend/ai/predict.py; public like /sensors/ingest for device clients."""
    return await _save_detection(detection, background_tasks)


@router.get("", response_model=list[DetectionOut])
async def list_detections(limit: int = 100, violations_only: bool = False,
                           current_user: dict = Depends(get_current_user)):
    query = {"is_violation": True} if violations_only else {}
    docs = await detections_collection.find(query).sort("timestamp", -1).limit(limit).to_list(limit)
    return [{**d, "id": str(d["_id"])} for d in docs]
