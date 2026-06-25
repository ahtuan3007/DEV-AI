"""
Extract raw video frames into data/frames/<ClassName>/ for YOLO labeling.

Supported input layouts:
  data/raw_videos/binh_thuong.mp4
  data/raw_videos/nam_tay_01.mov
  data/raw_videos/Nam_Tay/clip_001.mp4

Run:
  python training/01_extract_frames.py
  python training/01_extract_frames.py --clean --every-n 6 --max-per-video 800
"""

from __future__ import annotations

import argparse
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

import cv2

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_VIDEO_DIR = BASE_DIR / "data" / "raw_videos"
DEFAULT_FRAMES_DIR = BASE_DIR / "data" / "frames"

CLASS_ALIASES = {
    "binh_thuong": "Binh_Thuong",
    "binh-thuong": "Binh_Thuong",
    "normal": "Binh_Thuong",
    "nam_tay": "Nam_Tay",
    "nam-tay": "Nam_Tay",
    "fist": "Nam_Tay",
    "chi_ngon": "Chi_Ngon_Tro",
    "chi-ngon": "Chi_Ngon_Tro",
    "chi_ngon_tro": "Chi_Ngon_Tro",
    "chi-ngon-tro": "Chi_Ngon_Tro",
    "chi_con": "Chi_Ngon_Tro",
    "chi-con": "Chi_Ngon_Tro",
    "chi_con_tro": "Chi_Ngon_Tro",
    "chi-con-tro": "Chi_Ngon_Tro",
    "point": "Chi_Ngon_Tro",
    "xoe_tay": "Xoe_Tay",
    "xoe-tay": "Xoe_Tay",
    "open_hand": "Xoe_Tay",
    "open-hand": "Xoe_Tay",
}

CLASS_NAMES = ["Binh_Thuong", "Nam_Tay", "Chi_Ngon_Tro", "Xoe_Tay"]
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"}


@dataclass(frozen=True)
class VideoJob:
    path: Path
    class_name: str


def normalize_key(value: str) -> str:
    return value.strip().lower().replace(" ", "_")


def infer_class(video_path: Path, video_root: Path) -> str | None:
    """Infer the class from the parent folder first, then from the filename."""
    try:
        rel = video_path.relative_to(video_root)
        parts = rel.parts[:-1]
    except ValueError:
        parts = video_path.parts[:-1]

    for part in reversed(parts):
        class_name = CLASS_ALIASES.get(normalize_key(part))
        if class_name:
            return class_name

    stem = normalize_key(video_path.stem)
    for alias, class_name in CLASS_ALIASES.items():
        if stem == alias or stem.startswith(f"{alias}_") or stem.startswith(f"{alias}-"):
            return class_name
    return None


def discover_videos(video_dir: Path) -> tuple[list[VideoJob], list[Path]]:
    jobs: list[VideoJob] = []
    unknown: list[Path] = []

    for video_path in sorted(video_dir.rglob("*")):
        if not video_path.is_file() or video_path.suffix.lower() not in VIDEO_EXTENSIONS:
            continue
        class_name = infer_class(video_path, video_dir)
        if class_name is None:
            unknown.append(video_path)
            continue
        jobs.append(VideoJob(path=video_path, class_name=class_name))

    return jobs, unknown


def clean_frame_dirs(frames_dir: Path) -> None:
    for class_name in CLASS_NAMES:
        class_dir = frames_dir / class_name
        if class_dir.exists():
            shutil.rmtree(class_dir)


def extract_from_video(video_path: Path, class_name: str, frames_dir: Path, every_n: int, max_per_video: int) -> int:
    out_dir = frames_dir / class_name
    out_dir.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print(f"  [SKIP] Cannot open: {video_path}")
        return 0

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    print(f"  Video: {video_path.name} | {fps:.1f} fps | ~{total} frames | class={class_name}")

    saved = 0
    frame_idx = 0
    stem = video_path.stem

    while cap.isOpened() and saved < max_per_video:
        ok, frame = cap.read()
        if not ok:
            break
        if frame_idx % every_n == 0:
            out_name = f"{stem}_{saved:05d}.jpg"
            out_path = out_dir / out_name
            cv2.imwrite(str(out_path), frame)
            saved += 1
        frame_idx += 1

    cap.release()
    print(f"  -> Saved {saved} images to {out_dir}")
    return saved


def print_video_naming_help(video_dir: Path) -> None:
    print("Expected video names or folders:")
    print(f"  {video_dir / 'binh_thuong.mp4'}")
    print(f"  {video_dir / 'nam_tay.mp4'}")
    print(f"  {video_dir / 'chi_ngon.mp4'}")
    print(f"  {video_dir / 'xoe_tay.mp4'}")
    print("Or put clips inside class folders:")
    for class_name in CLASS_NAMES:
        print(f"  {video_dir / class_name / 'clip_001.mp4'}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract frames from raw gesture videos.")
    parser.add_argument("--video-dir", type=Path, default=DEFAULT_VIDEO_DIR)
    parser.add_argument("--frames-dir", type=Path, default=DEFAULT_FRAMES_DIR)
    parser.add_argument(
        "--every-n",
        type=int,
        default=6,
        help="Save one frame every N frames. Default 6 is about 5 fps for 30 fps video.",
    )
    parser.add_argument("--max-per-video", type=int, default=800, help="Maximum images saved per video.")
    parser.add_argument("--clean", action="store_true", help="Delete existing class frame folders before extracting.")
    args = parser.parse_args()

    video_dir = args.video_dir.resolve()
    frames_dir = args.frames_dir.resolve()
    video_dir.mkdir(parents=True, exist_ok=True)
    frames_dir.mkdir(parents=True, exist_ok=True)

    if args.every_n <= 0:
        raise SystemExit("--every-n must be greater than 0")
    if args.max_per_video <= 0:
        raise SystemExit("--max-per-video must be greater than 0")

    jobs, unknown = discover_videos(video_dir)

    print("=== EXTRACT FRAMES FROM RAW VIDEOS ===\n")
    if unknown:
        print("[WARN] These videos were ignored because class could not be inferred:")
        for path in unknown:
            print(f"  - {path}")
        print()

    if not jobs:
        print(f"No supported videos found in {video_dir}\n")
        print_video_naming_help(video_dir)
        return

    if args.clean:
        clean_frame_dirs(frames_dir)

    totals = {class_name: 0 for class_name in CLASS_NAMES}
    for job in jobs:
        totals[job.class_name] += extract_from_video(
            video_path=job.path,
            class_name=job.class_name,
            frames_dir=frames_dir,
            every_n=args.every_n,
            max_per_video=args.max_per_video,
        )

    print("\nFrame summary:")
    for class_name in CLASS_NAMES:
        print(f"  {class_name}: {totals[class_name]}")

    missing_classes = [class_name for class_name, count in totals.items() if count == 0]
    if missing_classes:
        print("\n[WARN] Missing frame output for: " + ", ".join(missing_classes))

    print(f"\nTotal: {sum(totals.values())} images in {frames_dir}")
    print("Next: upload data/frames to Roboflow, label hand bounding boxes, export YOLOv8.")


if __name__ == "__main__":
    main()
