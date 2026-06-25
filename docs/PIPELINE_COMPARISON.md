# So sánh pipeline train (chọn đúng cho Web App)

## Web App hiện tại cần gì?

- File model: `models/best.pt`
- Engine: **Ultralytics YOLO** (object detection, bounding box)
- 4 class (phải khớp tên):

| ID | Tên class | Cử chỉ | Hành động app |
|----|-----------|--------|----------------|
| 0 | `Binh_Thuong` | Tay nghỉ | Không kích hoạt |
| 1 | `Nam_Tay` | Nắm tay | Bật/tắt đèn |
| 2 | `Chi_Ngon_Tro` | Chỉ ngón trỏ | Chỉnh giường |
| 3 | `Xoe_Tay` | Xòe tay | SOS |

## Pipeline cũ trong `src/` (KHÔNG dùng cho app YOLO)

| File | Công nghệ | Đầu ra |
|------|-----------|--------|
| `src/1_collect_data.py` | MediaPipe landmark → CSV | `data/train.csv`, `val.csv` |
| `src/2_train_model.py` | RandomForest | `models/random_forest.pkl` |

**Kết luận:** Pipeline cũ phù hợp học ML cơ bản, nhưng **không** thay thế được `best.pt` cho `hospital_app`.

## Pipeline mới (YOLO + Colab) — DÙNG CÁI NÀY

```text
Quay video → Trích frame → Gán bbox (Roboflow) → dataset YOLO → Train Colab → best.pt
```

Công cụ trong repo:

- `training/01_extract_frames.py` — trích ảnh từ video
- `training/02_package_dataset.py` — đóng gói / chia train-val
- `training/colab_train.ipynb` — train trên Google Colab
- `docs/TRAINING_GUIDE.md` — hướng dẫn từng bước (tiếng Việt)
