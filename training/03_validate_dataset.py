"""
Validate a packaged YOLO dataset before uploading dataset.zip to Colab.

Run:
  python training/03_validate_dataset.py --dataset-dir dataset
"""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

DEFAULT_CLASS_NAMES = ["Binh_Thuong", "Nam_Tay", "Chi_Ngon_Tro", "Xoe_Tay"]
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def read_class_names(yaml_path: Path) -> list[str]:
    names: list[str] = []
    in_names = False
    for raw_line in yaml_path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if stripped == "names:":
            in_names = True
            continue
        if in_names and stripped and not raw_line.startswith((" ", "\t")):
            break
        if in_names and ":" in stripped:
            _, value = stripped.split(":", 1)
            names.append(value.strip().strip("'\""))
    return names or DEFAULT_CLASS_NAMES


def validate_label_file(label_path: Path, class_count: int) -> list[str]:
    errors: list[str] = []
    for line_number, line in enumerate(label_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) != 5:
            errors.append(f"{label_path}:{line_number} expected 5 YOLO columns, got {len(parts)}")
            continue
        try:
            class_id = int(float(parts[0]))
            coords = [float(value) for value in parts[1:]]
        except ValueError:
            errors.append(f"{label_path}:{line_number} contains non-numeric values")
            continue
        if class_id < 0 or class_id >= class_count:
            errors.append(f"{label_path}:{line_number} class id {class_id} is outside 0-{class_count - 1}")
        if any(value < 0.0 or value > 1.0 for value in coords):
            errors.append(f"{label_path}:{line_number} bbox values must be normalized between 0 and 1")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate YOLO dataset structure and label files.")
    parser.add_argument("--dataset-dir", type=Path, default=Path("dataset"))
    args = parser.parse_args()

    dataset_dir = args.dataset_dir.resolve()
    required_dirs = [
        dataset_dir / "images" / "train",
        dataset_dir / "images" / "val",
        dataset_dir / "labels" / "train",
        dataset_dir / "labels" / "val",
    ]
    missing = [path for path in required_dirs if not path.exists()]
    if missing:
        raise SystemExit("Missing dataset directories:\n" + "\n".join(f"  - {path}" for path in missing))

    yaml_path = dataset_dir / "data.yaml"
    if not yaml_path.exists():
        raise SystemExit(f"Missing {yaml_path}")
    class_names = read_class_names(yaml_path)

    total_images = 0
    total_labels = 0
    class_counts: Counter[int] = Counter()
    errors: list[str] = []

    for split in ["train", "val"]:
        image_dir = dataset_dir / "images" / split
        label_dir = dataset_dir / "labels" / split
        images = sorted(path for path in image_dir.iterdir() if path.suffix.lower() in IMAGE_EXTENSIONS)
        labels = sorted(label_dir.glob("*.txt"))
        total_images += len(images)
        total_labels += len(labels)

        label_names = {path.stem for path in labels}
        for image_path in images:
            if image_path.stem not in label_names:
                errors.append(f"Missing label for {image_path}")

        for label_path in labels:
            errors.extend(validate_label_file(label_path, len(class_names)))
            for line in label_path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    class_counts[int(float(line.split()[0]))] += 1

        print(f"{split}: {len(images)} images | {len(labels)} labels")

    if total_images == 0:
        errors.append("Dataset has no images")
    if total_labels == 0:
        errors.append("Dataset has no labels")

    print("\nClass label counts:")
    for class_id, class_name in enumerate(class_names):
        print(f"  {class_id} {class_name}: {class_counts[class_id]}")

    if errors:
        preview = "\n".join(f"  - {error}" for error in errors[:30])
        extra = "" if len(errors) <= 30 else f"\n  ... and {len(errors) - 30} more"
        raise SystemExit(f"\nDataset validation failed:\n{preview}{extra}")

    print("\nDataset validation passed.")


if __name__ == "__main__":
    main()
