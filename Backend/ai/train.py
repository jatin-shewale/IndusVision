import argparse
from pathlib import Path
from ultralytics import YOLO

AI_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = next(
    (parent for parent in AI_DIR.parents if (parent / "Worker-Safety").exists()),
    AI_DIR.parent,
)


def main():
    parser = argparse.ArgumentParser(description="Train YOLOv8 PPE detection model")
    parser.add_argument("--data", type=str, default=str(AI_DIR / "dataset.yaml"), help="Path to dataset.yaml")
    parser.add_argument("--model", type=str, default=str(PROJECT_ROOT / "Worker-Safety" / "yolov8n.pt"), help="Base model to fine-tune")
    parser.add_argument("--epochs", type=int, default=100, help="Number of training epochs")
    parser.add_argument("--imgsz", type=int, default=640, help="Image size")
    parser.add_argument("--batch", type=int, default=16, help="Batch size")
    parser.add_argument("--device", type=str, default="0", help="'0' for first GPU, 'cpu' for CPU")
    parser.add_argument("--project", type=str, default=str(AI_DIR / "runs"), help="Where to save runs")
    parser.add_argument("--name", type=str, default="indusvision_ppe", help="Run name")
    args = parser.parse_args()

    print(f"[INFO] Loading base model: {args.model}")
    model = YOLO(args.model)

    print("[INFO] Starting training...")
    results = model.train(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        project=args.project,
        name=args.name,
        patience=20,          # early stopping if no improvement
        save=True,
        plots=True,
        augment=True,
        val=True,
    )

    best_weights = Path(args.project) / args.name / "weights" / "best.pt"
    print(f"[DONE] Best model saved to: {best_weights}")
    print("Next step: run evaluate.py to check accuracy, then predict.py to test inference.")


if __name__ == "__main__":
    main()
