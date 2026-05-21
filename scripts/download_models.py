import argparse
import os
from pathlib import Path
from ultralytics import YOLO

def download_model(model_name):
    # Requirement: Save to models/yolo/ directory
    target_dir = Path("models/yolo")
    target_path = target_dir / f"{model_name}.pt"

    # Requirement: Handle case where model already exists
    if target_path.exists():
        print("Model already exists, skipping download.")
        return

    # Requirement: Create directory if needed
    target_dir.mkdir(parents=True, exist_ok=True)

    # Requirement: Print specific progress message
    # Mapping model names to user-friendly names for the print statement
    friendly_names = {"yolov8n": "nano", "yolov8s": "small", "yolov8m": "medium"}
    print(f"Downloading YOLOv8 {friendly_names.get(model_name, model_name)} model...")

    try:
        # Download using Ultralytics
        model = YOLO(f"{model_name}.pt")
        
        # Requirement: Save it to models/yolo/yolov8n.pt (move from root)
        if os.path.exists(f"{model_name}.pt"):
            os.rename(f"{model_name}.pt", target_path)
            
        # Requirement: Print success message
        print(f"✅ Model saved to {target_path}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    # Requirement: Add --model argument (yolov8n, yolov8s, yolov8m)
    parser = argparse.ArgumentParser(description="Download YOLOv8 models")
    parser.add_argument(
        "--model", 
        choices=["yolov8n", "yolov8s", "yolov8m"], 
        default="yolov8n", # Requirement: Default to yolov8n
        help="Choose model size"
    )
    args = parser.parse_args()
    download_model(args.model)