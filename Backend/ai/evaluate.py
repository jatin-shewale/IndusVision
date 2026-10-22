import argparse
from ultralytics import YOLO
from pathlib import Path

AI_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = next(
    (parent for parent in AI_DIR.parents if (parent / "Worker-Safety").exists()),
    AI_DIR.parent,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--weights", type=str, default=str(PROJECT_ROOT / "Worker-Safety" / "best.pt"), help="Path to trained .pt weights")
    parser.add_argument("--data", type=str, default=str(AI_DIR / "dataset.yaml"))
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--split", type=str, default="test", choices=["val", "test"])
    args = parser.parse_args()

    model = YOLO(args.weights)
    metrics = model.val(data=args.data, imgsz=args.imgsz, split=args.split)

    print("\n===== EVALUATION RESULTS =====")
    print(f"mAP50:    {metrics.box.map50:.4f}")
    print(f"mAP50-95: {metrics.box.map:.4f}")
    print(f"Precision: {metrics.box.mp:.4f}")
    print(f"Recall:    {metrics.box.mr:.4f}")
    print("Per-class results are saved in the runs/ output folder (confusion_matrix.png, PR_curve.png).")


if __name__ == "__main__":
    main()
