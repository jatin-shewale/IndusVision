import argparse
import time
from pathlib import Path

import cv2
from ultralytics import YOLO

VIOLATION_CLASSES = {"NO-Hardhat", "NO-Mask", "NO-Safety Vest"}
PROJECT_ROOT = next(
    (parent for parent in Path(__file__).resolve().parents if (parent / "Worker-Safety").exists()),
    Path(__file__).resolve().parents[1],
)
DEFAULT_WEIGHTS = PROJECT_ROOT / "Worker-Safety" / "best.pt"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--weights", type=str, default=str(DEFAULT_WEIGHTS),
        help=f"YOLO weights (default: the trained Worker-Safety model at {DEFAULT_WEIGHTS})",
    )
    parser.add_argument("--source", type=str, default="0", help="0=webcam, path, or rtsp:// url")
    parser.add_argument("--conf", type=float, default=0.5, help="Confidence threshold (matches the Worker-Safety live-camera notebook)")
    parser.add_argument("--save-dir", type=str, default=str(PROJECT_ROOT / "reports" / "screenshots"))
    parser.add_argument("--backend-url", type=str, default=None,
                         help="Optional: POST detections to e.g. http://localhost:8000/api/detections")
    args = parser.parse_args()

    Path(args.save_dir).mkdir(parents=True, exist_ok=True)
    model = YOLO(args.weights)

    # source "0" means default webcam
    source = 0 if args.source == "0" else args.source

    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print(f"[ERROR] Could not open source: {args.source}")
        return

    print("[INFO] Running inference. Press 'q' to quit.")
    while True:
        ok, frame = cap.read()
        if not ok:
            break

        results = model.predict(frame, conf=args.conf, verbose=False)
        r = results[0]
        annotated = r.plot()  # frame with boxes drawn

        violation_found = False
        detections = []
        for box in r.boxes:
            cls_name = model.names[int(box.cls[0])]
            confidence = float(box.conf[0])
            detections.append({"class": cls_name, "confidence": round(confidence, 3)})
            if cls_name in VIOLATION_CLASSES:
                violation_found = True

        if violation_found:
            ts = int(time.time())
            out_path = Path(args.save_dir) / f"violation_{ts}.jpg"
            cv2.imwrite(str(out_path), annotated)
            print(f"[ALERT] PPE violation detected -> saved {out_path} | {detections}")

            if args.backend_url:
                try:
                    import requests
                    requests.post(
                        args.backend_url,
                        json={
                            "camera_id": str(args.source),
                            "timestamp": ts,
                            "detections": [
                                {"class_name": item["class"], "confidence": item["confidence"]}
                                for item in detections
                            ],
                        },
                        timeout=2,
                    )
                except Exception as e:
                    print(f"[WARN] Could not reach backend: {e}")

        cv2.imshow("IndusVision - PPE Detection", annotated)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
