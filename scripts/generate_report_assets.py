"""
Tạo toàn bộ ảnh thống kê và biểu đồ cho báo cáo đồ án.
Model: best.pt (YOLOv8n, 3 class: Nam_Tay, Chi_Ngon_Tro, Xoe_Tay)
Dataset: dataset_3class/ (images/train, images/val, labels/train, labels/val)
Output: docs/assets/

Chạy:
    cd D:\DEV_AI
    .venv312\Scripts\python scripts\generate_report_assets.py
"""
from __future__ import annotations

import json
import random
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
from ultralytics import YOLO

# ═══════════════════════════════════════════════════════════════════
# CẤU HÌNH
# ═══════════════════════════════════════════════════════════════════
ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "dataset_3class"
OUT = ROOT / "docs" / "assets"
MODEL_PATH = ROOT / "best.pt"
EVAL_JSON = OUT / "evaluation_summary.json"

# 3 class trực tiếp từ model best.pt
CLASS_NAMES = ["Nam_Tay", "Chi_Ngon_Tro", "Xoe_Tay"]
CLASS_BY_ID = {0: "Nam_Tay", 1: "Chi_Ngon_Tro", 2: "Xoe_Tay"}
ACTION_MAP = {
    "Nam_Tay": "Bật/tắt đèn phòng",
    "Chi_Ngon_Tro": "Điều chỉnh giường bệnh",
    "Xoe_Tay": "SOS / Gọi y tá",
}
COLORS = {
    "Nam_Tay": "#10b981",
    "Chi_Ngon_Tro": "#3b82f6",
    "Xoe_Tay": "#ef4444",
}

plt.rcParams["font.family"] = "DejaVu Sans"


# ═══════════════════════════════════════════════════════════════════
# HÀM TIỆN ÍCH
# ═══════════════════════════════════════════════════════════════════
def iter_images(split: str) -> Iterable[Path]:
    image_dir = DATASET / "images" / split
    if not image_dir.exists():
        return []
    exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    return sorted(p for p in image_dir.iterdir() if p.suffix.lower() in exts)


def count_labels_from_txt(split: str) -> Counter:
    """Đếm số lượng nhãn từ file label YOLO (mỗi dòng = 1 object)."""
    label_dir = DATASET / "labels" / split
    counter = Counter()
    if not label_dir.exists():
        return counter
    for txt in label_dir.iterdir():
        if txt.suffix != ".txt":
            continue
        for line in txt.read_text(encoding="utf-8").splitlines():
            parts = line.strip().split()
            if len(parts) >= 5:
                cls_id = int(float(parts[0]))
                label = CLASS_BY_ID.get(cls_id)
                if label:
                    counter[label] += 1
    return counter


def collect_stats() -> tuple[dict, dict, Counter]:
    """Thu thập thống kê ảnh và nhãn theo split."""
    image_counts = {}
    label_counts = {}
    total_labels = Counter()
    for split in ("train", "val"):
        image_counts[split] = len(list(iter_images(split)))
        lc = count_labels_from_txt(split)
        label_counts[split] = lc
        total_labels += lc
    return image_counts, label_counts, total_labels


def xywhn_to_xyxy(box, w, h):
    cx, cy, bw, bh = box
    x1 = (cx - bw / 2) * w
    y1 = (cy - bh / 2) * h
    x2 = (cx + bw / 2) * w
    y2 = (cy + bh / 2) * h
    return x1, y1, x2, y2


def iou_xyxy(a, b) -> float:
    ix1, iy1 = max(a[0], b[0]), max(a[1], b[1])
    ix2, iy2 = min(a[2], b[2]), min(a[3], b[3])
    iw, ih = max(0.0, ix2 - ix1), max(0.0, iy2 - iy1)
    inter = iw * ih
    area_a = max(0.0, a[2] - a[0]) * max(0.0, a[3] - a[1])
    area_b = max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])
    union = area_a + area_b - inter
    return inter / union if union > 0 else 0.0


def read_gt_boxes(image_path: Path) -> list[dict]:
    split = image_path.parent.name
    label_path = DATASET / "labels" / split / f"{image_path.stem}.txt"
    image = cv2.imread(str(image_path))
    if image is None:
        return []
    h, w = image.shape[:2]
    boxes = []
    if not label_path.exists():
        return boxes
    for line in label_path.read_text(encoding="utf-8").splitlines():
        parts = line.strip().split()
        if len(parts) < 5:
            continue
        cls_id = int(float(parts[0]))
        label = CLASS_BY_ID.get(cls_id)
        if label is None:
            continue
        coords = [float(v) for v in parts[1:5]]
        boxes.append({"label": label, "box": xywhn_to_xyxy(coords, w, h)})
    return boxes


# ═══════════════════════════════════════════════════════════════════
# 1. THỐNG KÊ NHÃN - BIỂU ĐỒ CỘT
# ═══════════════════════════════════════════════════════════════════
def save_class_distribution(label_counts: dict) -> None:
    labels = CLASS_NAMES
    x = np.arange(len(labels))
    train = [label_counts["train"][l] for l in labels]
    val = [label_counts["val"][l] for l in labels]

    fig, ax = plt.subplots(figsize=(10.2, 5.4), dpi=170)
    width = 0.32
    bars1 = ax.bar(x - width / 2, train, width, label="Huấn luyện (Train)", color="#2563eb")
    bars2 = ax.bar(x + width / 2, val, width, label="Thử nghiệm (Val)", color="#f97316")
    ax.set_title("Thống kê số lượng nhãn theo lớp", fontsize=14, weight="bold")
    ax.set_ylabel("Số lượng nhãn (annotations)")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=11)
    ax.legend(frameon=False, fontsize=10)
    ax.grid(axis="y", alpha=0.25)
    ax.bar_label(bars1, fontsize=9, padding=2)
    ax.bar_label(bars2, fontsize=9, padding=2)
    fig.tight_layout()
    fig.savefig(OUT / "class_distribution.png")
    plt.close(fig)
    print("  ✅ class_distribution.png")


# ═══════════════════════════════════════════════════════════════════
# 2. TỶ LỆ CHIA TẬP - BIỂU ĐỒ TRÒN
# ═══════════════════════════════════════════════════════════════════
def save_split_distribution(image_counts: dict) -> None:
    sizes = [image_counts.get("train", 0), image_counts.get("val", 0)]
    labels = ["Huấn luyện (Train)", "Thử nghiệm (Val)"]
    colors = ["#2563eb", "#f97316"]
    total = sum(sizes)

    fig, ax = plt.subplots(figsize=(6.5, 5.6), dpi=170)
    ax.pie(
        sizes, labels=labels, colors=colors,
        autopct=lambda pct: f"{pct:.1f}%\n({int(round(pct * total / 100))})",
        startangle=90, textprops={"fontsize": 11},
    )
    ax.set_title("Tỷ lệ chia tập dữ liệu", fontsize=14, weight="bold")
    fig.tight_layout()
    fig.savefig(OUT / "split_distribution.png")
    plt.close(fig)
    print("  ✅ split_distribution.png")


# ═══════════════════════════════════════════════════════════════════
# 3. BẢNG THỐNG KÊ DATASET
# ═══════════════════════════════════════════════════════════════════
def save_dataset_table(image_counts: dict, label_counts: dict, total_labels: Counter) -> None:
    rows = []
    for label in CLASS_NAMES:
        rows.append([
            label,
            f"{label_counts['train'][label]:,}",
            f"{label_counts['val'][label]:,}",
            f"{total_labels[label]:,}",
        ])
    rows.append([
        "Tổng nhãn",
        f"{sum(label_counts['train'].values()):,}",
        f"{sum(label_counts['val'].values()):,}",
        f"{sum(total_labels.values()):,}",
    ])
    rows.append([
        "Tổng ảnh",
        f"{image_counts.get('train', 0):,}",
        f"{image_counts.get('val', 0):,}",
        f"{image_counts.get('train', 0) + image_counts.get('val', 0):,}",
    ])

    fig, ax = plt.subplots(figsize=(9.8, 3.7), dpi=180)
    ax.axis("off")
    ax.set_title("Bảng thống kê Dataset YOLOv8", fontsize=14, weight="bold", pad=12)
    table = ax.table(
        cellText=rows,
        colLabels=["Nhãn / Lớp", "Tập HL (Train)", "Tập Thử nghiệm (Val)", "Tổng"],
        cellLoc="center", loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.5)
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor("#cbd5e1")
        if row == 0:
            cell.set_facecolor("#1e293b")
            cell.set_text_props(color="white", weight="bold")
        elif row >= len(rows) - 1:
            cell.set_facecolor("#e2e8f0")
            cell.set_text_props(weight="bold")
        elif col == 0:
            cell.set_facecolor("#f8fafc")
    fig.tight_layout()
    fig.savefig(OUT / "dataset_summary_table.png")
    plt.close(fig)
    print("  ✅ dataset_summary_table.png")


# ═══════════════════════════════════════════════════════════════════
# 4. BẢNG LỰA CHỌN PHƯƠNG PHÁP
# ═══════════════════════════════════════════════════════════════════
def save_method_selection() -> None:
    rows = [
        ["YOLOv8 Object Detection", "BBox + class trong 1 lần suy luận", "✅ Phương pháp chính được sử dụng"],
        ["MediaPipe + RandomForest", "21 landmark tay + ML cổ điển", "Prototype ban đầu, dễ nhiễu"],
        ["CNN 1D", "Chuỗi landmark/đặc trưng 1 chiều", "So sánh lý thuyết"],
        ["CNN 2D", "Ảnh/frame RGB 2 chiều", "Nền tảng gần nhất với YOLO"],
        ["CNN 3D", "Chuỗi video theo thời gian", "Nặng, cần clip đã cắt sẵn"],
        ["Transformer (ViT)", "Self-Attention trên ảnh/chuỗi", "Mạnh nhưng cần nhiều dữ liệu"],
        ["CLIP (OpenAI)", "Ghép text + ảnh trong embedding", "Nghiên cứu liên quan (zero-shot)"],
    ]
    fig, ax = plt.subplots(figsize=(11, 5.7), dpi=170)
    ax.axis("off")
    ax.set_title("Lựa chọn phương pháp nhận diện cử chỉ tay", fontsize=15, weight="bold", pad=12)
    table = ax.table(
        cellText=rows,
        colLabels=["Phương pháp", "Ý tưởng chính", "Vai trò trong đồ án"],
        cellLoc="left", loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(9.2)
    table.scale(1, 1.55)
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor("#cbd5e1")
        if row == 0:
            cell.set_facecolor("#1e293b")
            cell.set_text_props(color="white", weight="bold")
        elif row == 1:
            cell.set_facecolor("#dcfce7")  # Highlight phương pháp chính
        elif row % 2 == 0:
            cell.set_facecolor("#f8fafc")
    fig.tight_layout()
    fig.savefig(OUT / "method_selection.png")
    plt.close(fig)
    print("  ✅ method_selection.png")


# ═══════════════════════════════════════════════════════════════════
# 5. SO SÁNH CÁC MÔ HÌNH
# ═══════════════════════════════════════════════════════════════════
def save_model_family_comparison() -> None:
    models = ["CNN 1D", "CNN 2D", "CNN 3D", "Transformer", "YOLOv8n\n(Đồ án)"]
    realtime = [4, 3, 2, 2, 5]
    data_need = [2, 3, 4, 5, 2]
    accuracy = [2, 3, 3, 5, 4]
    x = np.arange(len(models))
    width = 0.22

    fig, ax = plt.subplots(figsize=(10.5, 5.4), dpi=170)
    ax.bar(x - width, realtime, width, label="Tốc độ Realtime", color="#10b981")
    ax.bar(x, data_need, width, label="Nhu cầu dữ liệu", color="#f97316")
    ax.bar(x + width, accuracy, width, label="Độ chính xác", color="#3b82f6")
    ax.set_ylim(0, 5.8)
    ax.set_ylabel("Điểm đánh giá tương đối (1-5)")
    ax.set_title("So sánh các nhóm mô hình nhận diện cử chỉ tay", fontsize=15, weight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(models, fontsize=10)
    ax.grid(axis="y", alpha=0.25)
    ax.legend(frameon=False, fontsize=10)
    for bars in ax.containers:
        ax.bar_label(bars, fontsize=8.5)
    fig.tight_layout()
    fig.savefig(OUT / "model_family_comparison.png")
    plt.close(fig)
    print("  ✅ model_family_comparison.png")


# ═══════════════════════════════════════════════════════════════════
# 6. CLIP TEXT + ẢNH DIAGRAM
# ═══════════════════════════════════════════════════════════════════
def save_clip_diagram() -> None:
    fig, ax = plt.subplots(figsize=(10.6, 5.2), dpi=170)
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_title("CLIP: Kết hợp Text + Ảnh (Nghiên cứu liên quan)", fontsize=15, weight="bold", pad=12)
    boxes = [
        ("Ảnh bàn tay", 0.08, 0.62, 0.18, 0.16, "#dbeafe"),
        ("Image Encoder\n(ViT/ResNet)", 0.33, 0.62, 0.18, 0.16, "#e0f2fe"),
        ("Embedding\nchung", 0.58, 0.44, 0.18, 0.20, "#dcfce7"),
        ("Text prompt\n'nắm tay', 'xòe tay'", 0.08, 0.22, 0.18, 0.18, "#fee2e2"),
        ("Text Encoder\n(Transformer)", 0.33, 0.24, 0.18, 0.16, "#fef3c7"),
        ("So khớp Cosine\n→ Zero-shot", 0.78, 0.44, 0.16, 0.20, "#ede9fe"),
    ]
    arrows = [
        ((0.26, 0.70), (0.33, 0.70)),
        ((0.51, 0.70), (0.58, 0.56)),
        ((0.26, 0.31), (0.33, 0.31)),
        ((0.51, 0.31), (0.58, 0.52)),
        ((0.76, 0.54), (0.78, 0.54)),
    ]
    for text, x, y, w, h, color in boxes:
        rect = plt.Rectangle((x, y), w, h, linewidth=1.4, edgecolor="#334155", facecolor=color, zorder=2)
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=10, zorder=3)
    for start, end in arrows:
        ax.annotate("", xy=end, xytext=start, arrowprops={"arrowstyle": "->", "lw": 1.8, "color": "#334155"})
    ax.text(0.5, 0.08, "Đồ án sử dụng YOLOv8 (supervised) thay vì CLIP (zero-shot) vì cần tốc độ realtime và độ chính xác cao.",
            ha="center", fontsize=10, color="#334155")
    fig.tight_layout()
    fig.savefig(OUT / "clip_text_image.png")
    plt.close(fig)
    print("  ✅ clip_text_image.png")


# ═══════════════════════════════════════════════════════════════════
# 7. TRÍCH XUẤT ĐẶC TRƯNG PIPELINE
# ═══════════════════════════════════════════════════════════════════
def save_feature_extraction_diagram() -> None:
    fig, ax = plt.subplots(figsize=(11, 4.9), dpi=170)
    ax.axis("off")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_title("Pipeline trích xuất đặc trưng và suy luận YOLOv8", fontsize=15, weight="bold", pad=12)
    steps = [
        ("Frame\nWebcam/Video", "#dbeafe"),
        ("Resize\n640×640", "#e0f2fe"),
        ("Backbone\nCSPDarknet", "#dcfce7"),
        ("Neck\nPANet/FPN", "#fef3c7"),
        ("Detect Head\n3 class", "#fee2e2"),
        ("BBox +\nConfidence", "#ede9fe"),
        ("Action\nĐèn/Giường/SOS", "#fce7f3"),
    ]
    for i, (text, color) in enumerate(steps):
        x = 0.03 + i * 0.135
        rect = plt.Rectangle((x, 0.44), 0.108, 0.24, linewidth=1.3, edgecolor="#334155", facecolor=color, zorder=2)
        ax.add_patch(rect)
        ax.text(x + 0.054, 0.56, text, ha="center", va="center", fontsize=9.5, zorder=3)
        if i < len(steps) - 1:
            ax.annotate("", xy=(x + 0.133, 0.56), xytext=(x + 0.112, 0.56),
                         arrowprops={"arrowstyle": "->", "lw": 1.4})
    ax.text(0.5, 0.22, "YOLOv8n tự học đặc trưng từ ảnh huấn luyện, không cần trích xuất thủ công.",
            ha="center", fontsize=10, color="#334155")
    ax.text(0.5, 0.12, "t-SNE visualization lấy embedding từ layer 9 backbone để biểu diễn không gian đặc trưng.",
            ha="center", fontsize=10, color="#64748b")
    fig.tight_layout()
    fig.savefig(OUT / "feature_extraction_pipeline.png")
    plt.close(fig)
    print("  ✅ feature_extraction_pipeline.png")


# ═══════════════════════════════════════════════════════════════════
# 8. SƠ ĐỒ XÂY DỰNG HỆ THỐNG
# ═══════════════════════════════════════════════════════════════════
def save_architecture_diagram() -> None:
    boxes = [
        ("Webcam / Video", 0.04, 0.70, 0.15, 0.14, "#dbeafe"),
        ("OpenCV\nĐọc frame", 0.25, 0.70, 0.15, 0.14, "#e0f2fe"),
        ("YOLOv8n\nbest.pt (3 class)", 0.47, 0.66, 0.20, 0.22, "#dcfce7"),
        ("BBox + Class\nNam/Chi/Xoe", 0.74, 0.70, 0.20, 0.14, "#fef3c7"),
        ("Buffer + Dwell\nChống nhấp nháy", 0.17, 0.31, 0.22, 0.16, "#ede9fe"),
        ("Kiểm tra\nngưỡng tin cậy", 0.45, 0.31, 0.20, 0.16, "#fce7f3"),
        ("Hành động\nĐèn / Giường / SOS", 0.72, 0.31, 0.22, 0.16, "#fee2e2"),
    ]
    arrows = [
        ((0.19, 0.77), (0.25, 0.77)),
        ((0.40, 0.77), (0.47, 0.77)),
        ((0.67, 0.77), (0.74, 0.77)),
        ((0.84, 0.70), (0.28, 0.47)),
        ((0.39, 0.39), (0.45, 0.39)),
        ((0.65, 0.39), (0.72, 0.39)),
    ]

    fig, ax = plt.subplots(figsize=(11, 5.8), dpi=170)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_title("Sơ đồ xây dựng hệ thống nhận diện cử chỉ tay - Smart Hospital", fontsize=14, weight="bold", pad=16)

    for text, x, y, w, h, color in boxes:
        rect = plt.Rectangle((x, y), w, h, linewidth=1.4, edgecolor="#334155", facecolor=color, zorder=2)
        ax.add_patch(rect)
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=10, zorder=3)

    for start, end in arrows:
        ax.annotate("", xy=end, xytext=start, arrowprops={"arrowstyle": "->", "lw": 1.8, "color": "#334155"})

    ax.text(0.5, 0.12,
            "Model YOLOv8n huấn luyện trực tiếp 3 cử chỉ tay trên Google Colab (T4 GPU), triển khai CPU realtime.",
            ha="center", fontsize=10, color="#334155")
    fig.tight_layout()
    fig.savefig(OUT / "architecture_diagram.png")
    plt.close(fig)
    print("  ✅ architecture_diagram.png")


# ═══════════════════════════════════════════════════════════════════
# 9. ĐÁNH GIÁ MODEL TRÊN TẬP VAL
# ═══════════════════════════════════════════════════════════════════
def evaluate_model(model: YOLO) -> dict:
    image_paths = list(iter_images("val"))
    print(f"  Đánh giá model trên {len(image_paths)} ảnh val...")

    n_classes = len(CLASS_NAMES)
    confusion = np.zeros((n_classes, n_classes), dtype=int)
    # Binh_Thuong counts (no detection for an image that has GT, or detection on no-GT image)
    gt_count_by_class = Counter()
    detections_by_class: dict[str, list[dict]] = defaultdict(list)
    ious_for_correct = []
    no_gt_no_det = 0
    no_gt_has_det = 0
    has_gt_no_det = Counter()

    results = model.predict(
        [str(p) for p in image_paths],
        imgsz=640, conf=0.25, verbose=False, batch=8,
    )

    for image_path, result in zip(image_paths, results):
        gt_boxes = read_gt_boxes(image_path)
        gt_labels_in_image = [gt["label"] for gt in gt_boxes]
        for gl in gt_labels_in_image:
            gt_count_by_class[gl] += 1

        # Collect predictions
        preds = []
        if result.boxes is not None and len(result.boxes) > 0:
            for idx in range(len(result.boxes)):
                conf = float(result.boxes.conf[idx].item())
                cls_id = int(result.boxes.cls[idx].item())
                label = CLASS_BY_ID.get(cls_id)
                if label is None:
                    continue
                xyxy = tuple(float(v) for v in result.boxes.xyxy[idx].tolist())
                preds.append({"label": label, "conf": conf, "box": xyxy, "image": str(image_path)})
                detections_by_class[label].append(preds[-1])

        # Match predictions to ground truth for confusion matrix
        gt_matched = [False] * len(gt_boxes)
        pred_matched = [False] * len(preds)

        for pi, pred in enumerate(preds):
            best_iou = 0.0
            best_gi = -1
            for gi, gt in enumerate(gt_boxes):
                if gt_matched[gi]:
                    continue
                if gt["label"] != pred["label"]:
                    continue
                current_iou = iou_xyxy(pred["box"], gt["box"])
                if current_iou > best_iou:
                    best_iou = current_iou
                    best_gi = gi
            if best_gi >= 0 and best_iou >= 0.5:
                gt_matched[best_gi] = True
                pred_matched[pi] = True
                gt_cls = CLASS_NAMES.index(gt_boxes[best_gi]["label"])
                pred_cls = CLASS_NAMES.index(pred["label"])
                confusion[gt_cls, pred_cls] += 1
                ious_for_correct.append(best_iou)

        # Unmatched GTs = missed (false negatives) — not added to confusion as we don't have a "background" class
        for gi, gt in enumerate(gt_boxes):
            if not gt_matched[gi]:
                has_gt_no_det[gt["label"]] += 1

        # Unmatched predictions = false positives
        for pi, pred in enumerate(preds):
            if not pred_matched[pi]:
                # Cross-class confusion: find best IoU GT of different class
                best_iou = 0.0
                best_gi = -1
                for gi, gt in enumerate(gt_boxes):
                    current_iou = iou_xyxy(pred["box"], gt["box"])
                    if current_iou > best_iou:
                        best_iou = current_iou
                        best_gi = gi
                if best_gi >= 0 and best_iou >= 0.3:
                    gt_cls = CLASS_NAMES.index(gt_boxes[best_gi]["label"])
                    pred_cls = CLASS_NAMES.index(pred["label"])
                    confusion[gt_cls, pred_cls] += 1

    # Compute metrics
    accuracy, macro_f1, per_class_f1 = metrics_from_confusion(confusion)
    ap50, ap5095, ap_per_class = compute_map(detections_by_class, image_paths, gt_count_by_class)

    summary = {
        "classes": CLASS_NAMES,
        "confusion": confusion.tolist(),
        "accuracy": accuracy,
        "macro_f1": macro_f1,
        "per_class_f1": per_class_f1,
        "mean_iou_correct": float(np.mean(ious_for_correct)) if ious_for_correct else 0.0,
        "map50": ap50,
        "map5095": ap5095,
        "ap_per_class": ap_per_class,
        "val_images": len(image_paths),
        "missed_detections": dict(has_gt_no_det),
    }
    EVAL_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  ✅ evaluation_summary.json (Accuracy={accuracy:.3f}, mAP50={ap50:.3f}, mAP50-95={ap5095:.3f})")
    return summary


def compute_map(detections_by_class, image_paths, gt_count_by_class):
    gt_by_image = {str(path): read_gt_boxes(path) for path in image_paths}
    ap50_values = []
    ap5095_values = []
    ap_per_class = {}
    for label in CLASS_NAMES:
        aps = []
        for threshold in np.arange(0.5, 1.0, 0.05):
            aps.append(average_precision(label, detections_by_class[label], gt_by_image, gt_count_by_class[label], float(threshold)))
        ap_per_class[label] = {"ap50": aps[0] if aps else 0.0, "ap5095": float(np.mean(aps)) if aps else 0.0}
        ap50_values.append(aps[0] if aps else 0.0)
        ap5095_values.append(float(np.mean(aps)) if aps else 0.0)
    return (
        float(np.mean(ap50_values)) if ap50_values else 0.0,
        float(np.mean(ap5095_values)) if ap5095_values else 0.0,
        ap_per_class,
    )


def average_precision(label, detections, gt_by_image, gt_count, threshold):
    if gt_count == 0:
        return 0.0
    detections = sorted(detections, key=lambda d: d["conf"], reverse=True)
    matched = {}
    for image, boxes in gt_by_image.items():
        for idx, gt in enumerate(boxes):
            if gt["label"] == label:
                matched[(image, idx)] = False
    tp, fp = [], []
    for det in detections:
        candidates = [(idx, gt) for idx, gt in enumerate(gt_by_image.get(det["image"], [])) if gt["label"] == label]
        best_idx, best_iou = None, 0.0
        for idx, gt in candidates:
            cur = iou_xyxy(det["box"], gt["box"])
            if cur > best_iou:
                best_iou = cur
                best_idx = idx
        key = (det["image"], best_idx)
        if best_idx is not None and best_iou >= threshold and not matched.get(key, False):
            tp.append(1.0)
            fp.append(0.0)
            matched[key] = True
        else:
            tp.append(0.0)
            fp.append(1.0)
    if not tp:
        return 0.0
    tp_cum = np.cumsum(tp)
    fp_cum = np.cumsum(fp)
    recall = tp_cum / max(gt_count, 1)
    precision = tp_cum / np.maximum(tp_cum + fp_cum, 1e-12)
    return float(voc_ap(recall, precision))


def voc_ap(recall, precision):
    mrec = np.concatenate(([0.0], recall, [1.0]))
    mpre = np.concatenate(([0.0], precision, [0.0]))
    for i in range(mpre.size - 1, 0, -1):
        mpre[i - 1] = max(mpre[i - 1], mpre[i])
    idx = np.where(mrec[1:] != mrec[:-1])[0]
    return np.sum((mrec[idx + 1] - mrec[idx]) * mpre[idx + 1])


def metrics_from_confusion(confusion):
    total = confusion.sum()
    accuracy = float(np.trace(confusion) / total) if total else 0.0
    f1_scores = {}
    for i, label in enumerate(CLASS_NAMES):
        tp = confusion[i, i]
        fp = confusion[:, i].sum() - tp
        fn = confusion[i, :].sum() - tp
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        f1_scores[label] = float(f1)
    return accuracy, float(np.mean(list(f1_scores.values()))), f1_scores


# ═══════════════════════════════════════════════════════════════════
# 10. MA TRẬN NHẦM LẪN
# ═══════════════════════════════════════════════════════════════════
def save_confusion_matrix(eval_summary: dict, normalized: bool = False) -> None:
    matrix = np.array(eval_summary["confusion"], dtype=float)
    display = matrix.copy()
    if normalized:
        row_sums = display.sum(axis=1, keepdims=True)
        display = np.divide(display, np.maximum(row_sums, 1), out=np.zeros_like(display), where=row_sums > 0)

    fig, ax = plt.subplots(figsize=(6.6, 5.8), dpi=170)
    im = ax.imshow(display, cmap="Blues", vmin=0, vmax=1 if normalized else None)
    suffix = " (Chuẩn hóa)" if normalized else ""
    ax.set_title(f"Ma trận nhầm lẫn{suffix}", fontsize=14, weight="bold")
    ax.set_xlabel("Dự đoán (Predicted)")
    ax.set_ylabel("Nhãn thật (Ground Truth)")
    ax.set_xticks(np.arange(len(CLASS_NAMES)))
    ax.set_yticks(np.arange(len(CLASS_NAMES)))
    ax.set_xticklabels(CLASS_NAMES, rotation=20, ha="right")
    ax.set_yticklabels(CLASS_NAMES)
    for i in range(len(CLASS_NAMES)):
        for j in range(len(CLASS_NAMES)):
            text = f"{display[i, j]:.2f}" if normalized else str(int(matrix[i, j]))
            ax.text(j, i, text, ha="center", va="center", color="#0f172a", fontsize=11)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    name = "confusion_matrix_normalized.png" if normalized else "confusion_matrix.png"
    fig.savefig(OUT / name)
    plt.close(fig)
    print(f"  ✅ {name}")


# ═══════════════════════════════════════════════════════════════════
# 11. BẢNG CHỈ SỐ ĐÁNH GIÁ
# ═══════════════════════════════════════════════════════════════════
def save_metrics_summary(model: YOLO, eval_summary: dict, latency_ms: float) -> dict:
    try:
        params = sum(p.numel() for p in model.model.parameters())
    except Exception:
        params = 0
    try:
        from ultralytics.utils.torch_utils import get_flops
        flops_640 = float(get_flops(model.model, imgsz=640))
    except Exception:
        flops_640 = 0.0

    metrics = {
        "Accuracy": f"{eval_summary['accuracy']:.3f}",
        "F1-Score (Macro)": f"{eval_summary['macro_f1']:.3f}",
        "IoU (TB đúng)": f"{eval_summary['mean_iou_correct']:.3f}",
        "mAP@0.5": f"{eval_summary['map50']:.3f}",
        "mAP@0.5:0.95": f"{eval_summary['map5095']:.3f}",
        "FLOPs @640": f"{flops_640:.2f} GFLOPs",
        "Parameters": f"{params:,}",
        "Inference CPU": f"{latency_ms:.1f} ms @320",
    }

    # Per-class F1
    for cls in CLASS_NAMES:
        f1 = eval_summary["per_class_f1"].get(cls, 0.0)
        metrics[f"F1 {cls}"] = f"{f1:.3f}"

    rows = [[key, value] for key, value in metrics.items()]
    rows.extend([
        ["Model", "YOLOv8n (custom 3 class)"],
        ["Train imgsz", "640"],
        ["Train epochs", "50"],
        ["Train platform", "Google Colab T4 GPU"],
    ])

    fig, ax = plt.subplots(figsize=(8.8, 7.5), dpi=170)
    ax.axis("off")
    ax.set_title("Chỉ số thử nghiệm và đánh giá", fontsize=15, weight="bold", pad=12)
    table = ax.table(cellText=rows, colLabels=["Chỉ số", "Giá trị"], cellLoc="left", loc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.3)
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor("#cbd5e1")
        if row == 0:
            cell.set_facecolor("#1e293b")
            cell.set_text_props(color="white", weight="bold")
        elif row <= len(metrics):
            cell.set_facecolor("#f8fafc")
    fig.tight_layout()
    fig.savefig(OUT / "metrics_summary.png")
    plt.close(fig)
    print("  ✅ metrics_summary.png")
    return metrics


# ═══════════════════════════════════════════════════════════════════
# 12. t-SNE
# ═══════════════════════════════════════════════════════════════════
def pca_reduce(x, dims):
    x = x - x.mean(axis=0, keepdims=True)
    _, _, vt = np.linalg.svd(x, full_matrices=False)
    return x @ vt[:min(dims, vt.shape[0])].T


def pairwise_distances(x):
    sq = np.sum(x * x, axis=1)
    dist = sq[:, None] + sq[None, :] - 2 * x @ x.T
    return np.maximum(dist, 0)


def tsne(x, perplexity=12.0, iterations=500):
    n = x.shape[0]
    distances = pairwise_distances(x)
    p = np.zeros((n, n), dtype=np.float64)
    target_entropy = np.log(perplexity)

    for i in range(n):
        beta_min, beta_max = -np.inf, np.inf
        beta = 1.0
        mask = np.ones(n, dtype=bool)
        mask[i] = False
        di = distances[i, mask]
        for _ in range(40):
            pi = np.exp(-di * beta)
            sum_pi = max(pi.sum(), 1e-12)
            entropy = np.log(sum_pi) + beta * np.sum(di * pi) / sum_pi
            diff = entropy - target_entropy
            if abs(diff) < 1e-5:
                break
            if diff > 0:
                beta_min = beta
                beta = beta * 2 if beta_max == np.inf else (beta + beta_max) / 2
            else:
                beta_max = beta
                beta = beta / 2 if beta_min == -np.inf else (beta + beta_min) / 2
        p[i, mask] = pi / sum_pi

    p = (p + p.T) / (2 * n)
    p = np.maximum(p * 4.0, 1e-12)
    rng = np.random.default_rng(7)
    y = rng.normal(0, 1e-4, size=(n, 2))
    y_inc = np.zeros_like(y)
    momentum = 0.5

    for it in range(iterations):
        sum_y = np.sum(y * y, axis=1)
        num = 1 / (1 + np.maximum(sum_y[:, None] + sum_y[None, :] - 2 * y @ y.T, 0))
        np.fill_diagonal(num, 0)
        q = np.maximum(num / max(num.sum(), 1e-12), 1e-12)
        pq = p - q
        grad = np.zeros_like(y)
        for i in range(n):
            grad[i] = 4 * np.sum((pq[:, i] * num[:, i])[:, None] * (y[i] - y), axis=0)
        y_inc = momentum * y_inc - 180.0 * grad
        y += y_inc
        y -= y.mean(axis=0, keepdims=True)
        if it == 180:
            p /= 4.0
            momentum = 0.8
    return y


def save_tsne_plot(model: YOLO) -> None:
    print("  Đang tạo t-SNE plot...")
    random.seed(7)
    grouped: dict[str, list[Path]] = defaultdict(list)
    for split in ("train", "val"):
        for image in iter_images(split):
            label_path = DATASET / "labels" / split / f"{image.stem}.txt"
            if label_path.exists():
                for line in label_path.read_text(encoding="utf-8").splitlines():
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        cls_id = int(float(parts[0]))
                        cls = CLASS_BY_ID.get(cls_id)
                        if cls:
                            grouped[cls].append(image)
                            break

    sample_paths = []
    sample_labels = []
    for cls in CLASS_NAMES:
        paths = list(set(grouped[cls]))
        random.shuffle(paths)
        chosen = paths[:80]  # Tăng số lượng mẫu lên 80 ảnh/class để biểu đồ dày dặn và đẹp mắt hơn
        sample_paths.extend(chosen)
        sample_labels.extend([cls] * len(chosen))

    if len(sample_paths) < 6:
        print("  ⚠ Không đủ ảnh để tạo t-SNE")
        return

    features = []
    results = model.predict([str(p) for p in sample_paths], imgsz=320, verbose=False, embed=[9], batch=8)
    for result in results:
        vector = result.detach().cpu().numpy().astype(np.float64).reshape(-1)
        features.append(vector)
    x = np.vstack(features)
    x = (x - x.mean(axis=0, keepdims=True)) / (x.std(axis=0, keepdims=True) + 1e-9)
    x = pca_reduce(x, 24)
    y = tsne(x, perplexity=15.0, iterations=500)  # Điều chỉnh perplexity cho phù hợp với số lượng mẫu lớn hơn

    fig, ax = plt.subplots(figsize=(8.0, 6.6), dpi=180)
    
    # Vẽ các vùng ellipse tự tin (confidence ellipses) cho từng cụm đặc trưng
    from matplotlib.patches import Ellipse
    for cls in CLASS_NAMES:
        idx = [i for i, label in enumerate(sample_labels) if label == cls]
        val_x = y[idx, 0]
        val_y = y[idx, 1]
        
        # Tính toán ma trận hiệp biến và các giá trị riêng/vectơ riêng để vẽ ellipse tự tin 95%
        cov = np.cov(val_x, val_y)
        vals, vecs = np.linalg.eigh(cov)
        order = vals.argsort()[::-1]
        vals, vecs = vals[order], vecs[:, order]
        theta = np.degrees(np.arctan2(vecs[1, 0], vecs[0, 0]))
        
        # 2 độ lệch chuẩn (covers ~95% dữ liệu mẫu)
        w = 2 * np.sqrt(max(0.01, vals[0])) * 2.0
        h = 2 * np.sqrt(max(0.01, vals[1])) * 2.0
        
        ell = Ellipse(xy=(np.mean(val_x), np.mean(val_y)),
                      width=w, height=h, angle=theta,
                      edgecolor=COLORS[cls], facecolor=COLORS[cls], alpha=0.12, lw=1.5, ls="--")
        ax.add_patch(ell)

    # Vẽ các điểm scatter
    for cls in CLASS_NAMES:
        idx = [i for i, label in enumerate(sample_labels) if label == cls]
        ax.scatter(y[idx, 0], y[idx, 1], s=80, alpha=0.88, label=cls, color=COLORS[cls],
                   edgecolors="white", linewidth=0.8, zorder=3)
        
    ax.set_title("t-SNE: Không gian đặc trưng YOLOv8 (3 lớp cử chỉ)", fontsize=13, weight="bold", pad=15)
    ax.set_xlabel("t-SNE Dimension 1", fontsize=10, labelpad=8)
    ax.set_ylabel("t-SNE Dimension 2", fontsize=10, labelpad=8)
    ax.legend(frameon=True, facecolor="#f8fafc", edgecolor="#cbd5e1", fontsize=10, loc="upper right")
    ax.grid(alpha=0.15, ls=":")
    
    # Trang trí đường viền dày dặn chuyên nghiệp
    for spine in ax.spines.values():
        spine.set_linewidth(1.5)
        spine.set_edgecolor("#334155")
        
    fig.tight_layout()
    fig.savefig(OUT / "tsne_features.png")
    plt.close(fig)
    print("  ✅ tsne_features.png (Đã nâng cấp đồ họa đẹp mắt)")


# ═══════════════════════════════════════════════════════════════════
# 13. ĐO LATENCY
# ═══════════════════════════════════════════════════════════════════
def measure_latency(model: YOLO, size: int = 320, repeats: int = 5) -> float:
    device = next(model.model.parameters()).device
    tensor = torch.zeros(1, 3, size, size, device=device)
    model.model.eval()
    with torch.no_grad():
        model.model(tensor)  # warmup
        start = time.perf_counter()
        for _ in range(repeats):
            model.model(tensor)
    return (time.perf_counter() - start) / repeats * 1000


# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════
def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"❌ Model không tìm thấy: {MODEL_PATH}")

    print("=" * 60)
    print("  TẠO ẢNH THỐNG KÊ CHO BÁO CÁO ĐỒ ÁN")
    print(f"  Model : {MODEL_PATH}")
    print(f"  Dataset: {DATASET}")
    print(f"  Output : {OUT}")
    print("=" * 60)

    # Thu thập thống kê dataset
    print("\n[1/7] Thống kê dataset...")
    image_counts, label_counts, total_labels = collect_stats()
    save_class_distribution(label_counts)
    save_split_distribution(image_counts)
    save_dataset_table(image_counts, label_counts, total_labels)

    # Biểu đồ lý thuyết
    print("\n[2/7] Biểu đồ lựa chọn phương pháp...")
    save_method_selection()
    save_model_family_comparison()
    save_clip_diagram()

    # Pipeline và kiến trúc
    print("\n[3/7] Sơ đồ trích xuất đặc trưng và kiến trúc...")
    save_feature_extraction_diagram()
    save_architecture_diagram()

    # Load model
    print("\n[4/7] Load model và đánh giá trên tập val...")
    model = YOLO(str(MODEL_PATH))
    print(f"  Model classes: {model.names}")

    # Đánh giá
    eval_summary = evaluate_model(model)

    # Ma trận nhầm lẫn
    print("\n[5/7] Ma trận nhầm lẫn...")
    save_confusion_matrix(eval_summary, normalized=False)
    save_confusion_matrix(eval_summary, normalized=True)

    # Metrics
    print("\n[6/7] Bảng chỉ số đánh giá...")
    latency_ms = measure_latency(model, size=320, repeats=5)
    print(f"  Inference latency CPU @320: {latency_ms:.1f} ms")
    metrics = save_metrics_summary(model, eval_summary, latency_ms)

    # t-SNE
    print("\n[7/7] t-SNE visualization...")
    save_tsne_plot(model)

    # Xóa ảnh cũ không còn dùng
    old_files = [
        "confusion_matrix_mapped.png",
        "confusion_matrix_mapped_normalized.png",
        "model_mapping_asl_to_gestures.png",
    ]
    for f in old_files:
        p = OUT / f
        if p.exists():
            p.unlink()
            print(f"  🗑 Xóa ảnh cũ: {f}")

    print("\n" + "=" * 60)
    print("  HOÀN TẤT! Tất cả ảnh đã được lưu vào:")
    print(f"  {OUT}")
    print("=" * 60)
    print("\nDanh sách ảnh đã tạo:")
    for p in sorted(OUT.glob("*.png")):
        print(f"  📊 {p.name}")


if __name__ == "__main__":
    main()
