"""Worker-Safety detection log API models."""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class DetectionItem(BaseModel):
    class_name: str
    confidence: float


class DetectionIn(BaseModel):
    """Matches the payload Backend/ai/predict.py sends when PPE violations are found."""
    camera_id: str = "CAM_01"
    machine_zone: Optional[str] = None
    timestamp: Optional[int] = None  # unix epoch from predict.py; server also stamps its own
    detections: List[DetectionItem]
    screenshot_path: Optional[str] = None


class DetectionOut(BaseModel):
    id: str
    camera_id: str
    machine_zone: Optional[str] = None
    detections: List[DetectionItem]
    screenshot_path: Optional[str] = None
    is_violation: bool
    timestamp: datetime


VIOLATION_CLASSES = {"NO-Hardhat", "NO-Mask", "NO-Safety Vest"}
