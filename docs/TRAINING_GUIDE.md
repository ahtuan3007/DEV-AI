# Hướng dẫn train YOLO cử chỉ tay (từng bước, người mới)

Tài liệu này kết hợp workflow Google Colab (Gemini) + bổ sung trích frame, gán nhãn bbox, `data.yaml` chuẩn.

**Đọc thêm:** [PIPELINE_COMPARISON.md](PIPELINE_COMPARISON.md) | [FILMING_PROTOCOL.md](FILMING_PROTOCOL.md)

---

## Tổng quan 6 giai đoạn

| # | Việc làm | Công cụ | Kết quả |
|---|----------|---------|---------|
| 1 | Quay video | Điện thoại/webcam | 4 file `.mp4` |
| 2 | Trích frame | `training/01_extract_frames.py` | `data/frames/` |
| 3 | Gán bbox | Roboflow | Export YOLOv8 |
| 4 | Đóng gói dataset | `training/02_package_dataset.py` | `dataset/` + zip |
| 5 | Train | Colab + `training/colab_train.ipynb` | `best.pt` |
| 6 | Deploy | Copy vào `models/` | App nhận diện |

---

## Giai đoạn 1 — Quay video

Xem chi tiết: [FILMING_PROTOCOL.md](FILMING_PROTOCOL.md)

Đặt 4 file vào `data/raw_videos/`:

- `binh_thuong.mp4`
- `nam_tay.mp4`
- `chi_ngon.mp4`
- `xoe_tay.mp4`

---

## Giai đoạn 2 — Trích frame (máy tính)

Mở terminal tại thư mục `DEV_AI`:

```bash
pip install opencv-python
python training/01_extract_frames.py
```

Tùy chỉnh:

```bash
python training/01_extract_frames.py --every-n 6 --max-per-video 800
```

Ảnh ra tại `data/frames/Binh_Thuong/`, `Nam_Tay/`, ...

---

## Giai đoạn 3 — Gán nhãn bbox (Roboflow)

YOLO cần **khung vuông quanh tay**, không chỉ tên class.

### Từng nút bấm trên Roboflow

1. Mở https://roboflow.com → **Sign Up** / đăng nhập.
2. **Create New Project**.
3. Project Type: **Object Detection**.
4. Project Name: ví dụ `smart-hospital-gesture`.
5. **Create Project**.
6. **Upload** → chọn toàn bộ ảnh trong `data/frames/` (hoặc từng thư mục class).
7. Vào **Annotate**:
   - Chọn ảnh.
   - Kéo box bao trọn bàn tay + cổ tay.
   - Chọn class: `Binh_Thuong`, `Nam_Tay`, `Chi_Ngon_Tro`, hoặc `Xoe_Tay`.
   - **Save** → ảnh tiếp theo.
8. Khi xong ~80% ảnh, vào **Generate** → **Continue**.
9. Preprocessing/Augmentation: có thể **Continue** (mặc định) lần đầu.
10. **Export** → Format: **YOLOv8** → **Download zip**.
11. Giải nén zip vào ví dụ `data/roboflow_export/`.

### Quy tắc vẽ box

- Box ôm sát tay.
- Ảnh mờ / tay mất → xóa, không label.
- Thống nhất 1 tay chính trong toàn bộ dataset.

---

## Giai đoạn 4 — Đóng gói dataset

```bash
python training/02_package_dataset.py --source data/roboflow_export --clean
```

Tạo:

```text
dataset/
  data.yaml
  images/train/
  images/val/
  labels/train/
  labels/val/
```

Nén `dataset/` → `dataset.zip` → upload **Google Drive** → `MyDrive/SmartHospital/dataset.zip`.

---

## Giai đoạn 5 — Train trên Google Colab

### Bật GPU

1. https://colab.research.google.com
2. **File → Upload notebook** → chọn `training/colab_train.ipynb`
3. **Runtime → Change runtime type**
4. Hardware accelerator: **T4 GPU**
5. **Save**

### Chạy notebook

1. Cell 1: Mount Drive → Allow.
2. Cell 2: Copy + unzip dataset.
3. Cell 3: Cài Ultralytics, kiểm tra CUDA.
4. Cell 4: Train (~20–45 phút).
5. Cell 5: Validation (mAP).
6. Cell 6: Copy `best.pt` về Drive.

Hoặc chạy CLI (1 cell):

```bash
!yolo task=detect mode=train model=yolov8n.pt data=/content/dataset/data.yaml epochs=100 imgsz=640 batch=16 device=0
```

---

## Giai đoạn 6 — Đưa model vào Web App

1. Tải `best.pt` từ Drive.
2. Copy vào `models/best.pt`:

```powershell
.\scripts\deploy_best_pt.ps1 -SourcePath "C:\Users\...\Downloads\best.pt"
```

3. Chạy app:

```bash
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

4. Mở http://127.0.0.1:8000 → **Start Camera** (webcam chỉ bật khi bạn bấm).
5. Test: giữ cử chỉ **5 giây** mới kích hoạt.

---

## So với bản Gemini — khác gì?

| Gemini | Bản kết hợp (repo này) |
|--------|-------------------------|
| Cấu trúc dataset + Colab train | Giữ nguyên |
| `data.yaml` path `../train/images` | Dùng `path: /content/dataset` + `images/train` (ít lỗi hơn) |
| Không nói trích frame từ video | Có `01_extract_frames.py` |
| Không nói gán bbox | Có hướng dẫn Roboflow chi tiết |
| Không chia theo session | `02_package_dataset.py` chia theo nhóm video |

---

## Checklist nghiệm thu

- [ ] 4 video đã quay đủ biến thể
- [ ] ≥400 ảnh/class sau trích frame
- [ ] Label bbox trên Roboflow
- [ ] `dataset.zip` upload Drive
- [ ] Colab train xong 100 epochs
- [ ] `best.pt` trong `models/`
- [ ] App test 4 cử chỉ + dwell 5s + SOS loop

---

## Lỗi thường gặp

| Lỗi | Cách xử lý |
|-----|------------|
| `Model file not found` | Đặt `models/best.pt` |
| Train Colab OOM | Giảm `batch=8` hoặc `imgsz=416` |
| Nhầm Chi_Ngon vs Nam_Tay | Thêm ảnh label sạch, train lại |
| Webcam tự bật | Chỉ bấm **Start Camera** trên UI |
