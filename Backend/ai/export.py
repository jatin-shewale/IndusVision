import argparse
from pathlib import Path
from ultralytics import YOLO

AI_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = next(
    (parent for parent in AI_DIR.parents if (parent / "Worker-Safety").exists()),
    AI_DIR.parent,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--weights", type=str, default=str(PROJECT_ROOT / "Worker-Safety" / "best.pt"))
    parser.add_argument("--format", type=str, default="onnx",
                         choices=["onnx", "torchscript", "engine", "openvino"],
                         help="onnx = universal/fast CPU inference; engine = TensorRT (NVIDIA GPU only)")
    args = parser.parse_args()

    model = YOLO(args.weights)
    path = model.export(format=args.format)
    print(f"[DONE] Exported model to: {path}")


if __name__ == "__main__":
    main()
