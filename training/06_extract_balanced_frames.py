"""
Extract a balanced number of frames per gesture class.

This is intended for the current workflow:
  data/raw_videos/Binh_Thuong/*.mp4
  data/raw_videos/Nam_Tay/*.mp4
  data/raw_videos/Chi_Ngon_Tro/*.mp4
  data/raw_videos/Xoe_Tay/*.mp4

NegativeBackground is intentionally ignored because it is not a gesture class.

Run:
  python training/06_extract_balanced_frames.py --clean --target-per-class 560
"""

from __future__ import annotations

import argparse
import math
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

import cv2

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw_videos"
FRAMES_DIR = BASE_DIR / "data" / "frames"

CLASS_NAMES = ["Binh_Thuong", "Nam_Tay", "Chi_Ngon_Tro", "Xoe_Tay"]
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"}


@dataclass(frozen=True)
class VideoInfo:
    path: Path
    frame_count: int
    fps: float


def safe_stem(path: Path) -> str:
    value = re.sub(r"[^A-Za-z0-9]+", "_", path.stem).strip("_")
    return value or "clip"


def get_video_info(path: Path) -> VideoInfo | None:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        print(f"[SKIP] Cannot open video: {path}")
        return None
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
    cap.release()
    if frame_count <= 0:
        print(f"[SKIP] Empty video: {path}")
        return None
    return VideoInfo(path=path, frame_count=frame_count, fps=fps)


def discover_class_videos(raw_dir: Path, class_name: str) -> list[VideoInfo]:
    class_dir = raw_dir / class_name
    if not class_dir.exists():
        return []
    videos: list[VideoInfo] = []
    for path in sorted(class_dir.rglob("*")):
        if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS:
            info = get_video_info(path)
            if info is not None:
                videos.append(info)
    return videos


def allocate_counts(videos: list[VideoInfo], target: int) -> dict[Path, int]:
    total_frames = sum(video.frame_count for video in videos)
    if total_frames <= 0:
        return {}
    target = min(target, total_frames)

    raw_allocations = [
        (video, (video.frame_count / total_frames) * target)
        for video in videos
    ]
    allocations = {video.path: int(math.floor(raw)) for video, raw in raw_allocations}
    assigned = sum(allocations.values())
    remainder = target - assigned

    by_fraction = sorted(
        raw_allocations,
        key=lambda item: item[1] - math.floor(item[1]),
        reverse=True,
    )
    for video, _ in by_fraction[:remainder]:
        allocations[video.path] += 1

    return allocations


def sample_indices(frame_count: int, count: int) -> list[int]:
    if count <= 0:
        return []
    if count >= frame_count:
        return list(range(frame_count))
    if count == 1:
        return [frame_count // 2]

    step = (frame_count - 1) / (count - 1)
    indices = sorted({int(round(i * step)) for i in range(count)})

    cursor = 0
    while len(indices) < count and cursor < frame_count:
        if cursor not in indices:
            indices.append(cursor)
        cursor += 1
    return sorted(indices[:count])


def extract_selected_frames(video: VideoInfo, class_name: str, out_dir: Path, count: int, clip_index: int) -> int:
    selected = set(sample_indices(video.frame_count, count))
    if not selected:
        return 0

    cap = cv2.VideoCapture(str(video.path))
    if not cap.isOpened():
        print(f"[SKIP] Cannot reopen video: {video.path}")
        return 0

    stem = safe_stem(video.path)
    saved = 0
    frame_index = 0
    while cap.isOpened() and saved < len(selected):
        ok, frame = cap.read()
        if not ok or frame is None:
            break
        if frame_index in selected:
            out_name = f"{class_name.lower()}_{clip_index:02d}_{stem}_{saved:04d}.jpg"
            cv2.imwrite(str(out_dir / out_name), frame)
            saved += 1
        frame_index += 1

    cap.release()
    return saved


def clean_frames(frames_dir: Path) -> None:
    for class_name in CLASS_NAMES:
        class_dir = frames_dir / class_name
        if class_dir.exists():
            shutil.rmtree(class_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract balanced gesture frames from raw videos.")
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--frames-dir", type=Path, default=FRAMES_DIR)
    parser.add_argument("--target-per-class", type=int, default=560)
    parser.add_argument("--class-name", action="append", choices=CLASS_NAMES, help="Only process this class. Repeat if needed.")
    parser.add_argument("--clean", action="store_true")
    args = parser.parse_args()

    if args.target_per_class <= 0:
        raise SystemExit("--target-per-class must be greater than 0")

    raw_dir = args.raw_dir.resolve()
    frames_dir = args.frames_dir.resolve()
    frames_dir.mkdir(parents=True, exist_ok=True)

    selected_classes = args.class_name or CLASS_NAMES

    if args.clean:
        for class_name in selected_classes:
            class_dir = frames_dir / class_name
            if class_dir.exists():
                shutil.rmtree(class_dir)

    print("=== BALANCED FRAME EXTRACTION ===")
    print(f"Raw videos: {raw_dir}")
    print(f"Output: {frames_dir}")
    print(f"Target per class: {args.target_per_class}\n")

    final_counts: dict[str, int] = {}
    for class_name in selected_classes:
        videos = discover_class_videos(raw_dir, class_name)
        out_dir = frames_dir / class_name
        out_dir.mkdir(parents=True, exist_ok=True)

        print(f"[{class_name}] {len(videos)} videos")
        if not videos:
            final_counts[class_name] = 0
            print("  [WARN] No videos found\n")
            continue

        total_frames = sum(video.frame_count for video in videos)
        print(f"  Total source frames: {total_frames}")
        allocations = allocate_counts(videos, args.target_per_class)

        class_saved = 0
        for clip_index, video in enumerate(videos, start=1):
            count = allocations.get(video.path, 0)
            saved = extract_selected_frames(video, class_name, out_dir, count, clip_index)
            class_saved += saved
            print(f"  {video.path.name}: {video.frame_count} frames @ {video.fps:.1f} fps -> {saved} images")

        final_counts[class_name] = class_saved
        print(f"  => Saved {class_saved} images\n")

    print("Final summary:")
    for class_name in selected_classes:
        print(f"  {class_name}: {final_counts.get(class_name, 0)}")
    print(f"\nDone. Upload these folders to Roboflow for labeling: {frames_dir}")


if __name__ == "__main__":
    main()
