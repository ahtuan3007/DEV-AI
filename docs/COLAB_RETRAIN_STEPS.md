# Kich ban train lai tren Google Colab

> NOTE 2026-06-04: Huong hien tai da chot bo bbox `Binh_Thuong`.
> Dung guide moi: `docs/COLAB_RETRAIN_3CLASS.md`
> va notebook moi: `training/colab_train_3class.ipynb`.
> File upload moi la `dataset_3class.zip`, khong phai `dataset.zip`.

## 1. Dataset frame hien tai

Anh da cat can bang tai:

```text
D:\DEV_AI\data\frames
```

So luong:

```text
Binh_Thuong     560
Chi_Ngon_Tro    560
Nam_Tay         560
Xoe_Tay         560
```

Khong dung `NegativeBackground` trong lan train nay.

## 2. Dan nhan tren Roboflow

Tao project Object Detection, upload 4 folder trong `data\frames`.

Tao dung 4 class:

```text
Binh_Thuong
Nam_Tay
Chi_Ngon_Tro
Xoe_Tay
```

Quy tac label:

- Ve box om tron ban tay va mot phan co tay neu co.
- Khong ve ca nguoi/canh tay qua dai.
- Anh mo qua, mat tay, tay qua kho nhin thi xoa hoac khong dua vao dataset.
- Neu anh co 1 ban tay chinh thi ve 1 box.
- Neu co 2 tay nhung chi 1 tay lam cu chi, ve tay dang lam cu chi.

Sau khi xong, export format:

```text
YOLOv8
```

Giai nen export vao:

```text
D:\DEV_AI\data\roboflow_export\retrain_v2
```

## 3. Gop dataset sau khi export Roboflow

Chay tren may:

```powershell
cd D:\DEV_AI
.\.venv\Scripts\python.exe training\04_merge_roboflow_exports.py --source data\roboflow_export\retrain_v2 --clean --zip-output dataset\dataset.zip
```

Ket qua can co:

```text
D:\DEV_AI\dataset
D:\DEV_AI\dataset\dataset.zip
```

## 4. Upload len Google Drive

Upload:

```text
D:\DEV_AI\dataset\dataset.zip
```

Len:

```text
MyDrive/SmartHospital/dataset.zip
```

## 5. Train tren Colab

Mo:

```text
D:\DEV_AI\training\colab_train.ipynb
```

Trong Colab:

```text
Runtime -> Change runtime type -> T4 GPU -> Save
```

Chay lan luot cac cell trong notebook.

Neu muon chay bang cell rieng, dung:

```python
from google.colab import drive
drive.mount('/content/drive')
```

```bash
!cp "/content/drive/MyDrive/SmartHospital/dataset.zip" /content/
!rm -rf /content/dataset
!unzip -q /content/dataset.zip -d /content/
!cat /content/dataset/data.yaml
```

```bash
!pip install ultralytics -q
```

```python
from ultralytics import YOLO

model = YOLO("yolov8n.pt")
results = model.train(
    data="/content/dataset/data.yaml",
    epochs=100,
    imgsz=640,
    batch=16,
    device=0,
    patience=20,
    project="/content/runs",
    name="gesture_retrain_v2",
)
```

```python
from ultralytics import YOLO

best_path = "/content/runs/gesture_retrain_v2/weights/best.pt"
model = YOLO(best_path)
metrics = model.val(data="/content/dataset/data.yaml")
print(metrics)
```

```bash
!mkdir -p "/content/drive/MyDrive/SmartHospital"
!cp /content/runs/gesture_retrain_v2/weights/best.pt "/content/drive/MyDrive/SmartHospital/best.pt"
```

## 6. Sau khi train xong

Tai `best.pt` tu Drive ve va thay vao:

```text
D:\DEV_AI\models\best.pt
```

Sau do test terminal:

```powershell
cd D:\DEV_AI
.\scripts\run_terminal_test.cmd
```
