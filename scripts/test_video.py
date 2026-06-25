from ultralytics import YOLO
import cv2
import sys
from pathlib import Path

def test_video(video_path, model_path="D:/DEV_AI/best.pt"):
    video_path = Path(video_path)
    if not video_path.exists():
        print(f"Error: Video file not found at {video_path}")
        return

    print(f"Loading model from {model_path}...")
    model = YOLO(model_path)
    
    # Run prediction and save the annotated video
    print(f"Processing video: {video_path}")
    results = model.predict(
        source=str(video_path),
        save=True,  # Ultralytics will save to runs/detect/predict/
        conf=0.25,  # Set a lower confidence threshold to see what it detects
        device="cpu"  # Try CPU
    )
    print("Done! The annotated video is saved in the runs/detect/ folder.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_video.py <path_to_video>")
    else:
        test_video(sys.argv[1])
