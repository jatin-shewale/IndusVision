"""Lazy-loaded PPE inference using the trained Worker-Safety weights."""
from functools import lru_cache
from pathlib import Path
from threading import Lock

import cv2
import numpy as np
from ultralytics import YOLO

from app.config import settings

_INFERENCE_LOCK = Lock()


@lru_cache(maxsize=1)
def _load_model() -> YOLO:
    weights = Path(settings.PPE_MODEL_PATH).expanduser()
    if not weights.is_file():
        raise FileNotFoundError(
            f"PPE model weights not found at {weights}. Set PPE_MODEL_PATH or restore Worker-Safety/best.pt."
        )
    return YOLO(str(weights))


def infer_image(image_bytes: bytes, confidence: float = 0.4) -> tuple[list[dict], bytes]:
    """Run one image through the trained model and return detections and annotated JPEG bytes."""
    image = cv2.imdecode(np.frombuffer(image_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Uploaded file is not a readable image")

    with _INFERENCE_LOCK:
        model = _load_model()
        result = model.predict(image, conf=confidence, verbose=False)[0]
    detections = [
        {
            "class_name": model.names[int(box.cls[0])],
            "confidence": round(float(box.conf[0]), 4),
        }
        for box in result.boxes
    ]
    ok, encoded = cv2.imencode(".jpg", result.plot())
    if not ok:
        raise RuntimeError("Could not encode annotated image")
    return detections, encoded.tobytes()
