# YOLO Training Workflow

Current retrain target: use `training/colab_train_3class.ipynb` with
`dataset_3class.zip`. Do not train `Binh_Thuong` as a bbox class; keep it as
background/idle.

This folder is set up so you can record videos later, drop them into `data/raw_videos/`,
extract frames, label in Roboflow, package a YOLO dataset, and train on Colab.

## 0. Prepare folders

```powershell
.\scripts\setup_training_workspace.cmd
```

If Python was reinstalled or `.venv` is broken, install Python 3.11+ first, then run:

```powershell
.\scripts\rebuild_venv.cmd
```

## 1. Drop raw videos

Use either one file per class:

```text
data/raw_videos/binh_thuong.mp4
data/raw_videos/nam_tay.mp4
data/raw_videos/chi_ngon.mp4
data/raw_videos/xoe_tay.mp4
```

Or multiple clips inside class folders:

```text
data/raw_videos/Binh_Thuong/clip_001.mp4
data/raw_videos/Nam_Tay/clip_001.mp4
data/raw_videos/Chi_Ngon_Tro/clip_001.mp4
data/raw_videos/Xoe_Tay/clip_001.mp4
```

Supported video extensions: `.mp4`, `.mov`, `.avi`, `.mkv`, `.webm`, `.m4v`.

## 2. Extract frames

```powershell
.\scripts\extract_after_recording.cmd -Clean
```

Output:

```text
data/frames/Binh_Thuong/
data/frames/Nam_Tay/
data/frames/Chi_Ngon_Tro/
data/frames/Xoe_Tay/
```

## 3. Label in Roboflow

Upload `data/frames/`, create bounding boxes around the active hand, then export YOLOv8.
Unzip the Roboflow export into:

```text
data/roboflow_export/
```

## 4. Package dataset for Colab

```powershell
.\scripts\package_roboflow.cmd -Source data\roboflow_export -Clean
```

This creates:

```text
dataset/
dataset.zip
```

Upload `dataset.zip` to Google Drive at:

```text
MyDrive/SmartHospital/dataset.zip
```

## 5. Train on Colab

Open `training/colab_train.ipynb`, run all cells, then copy the produced `best.pt` into:

```text
models/best.pt
```

## Dynamic gestures later

Do not mix dynamic gestures like circle drawing or air tapping into this static YOLO dataset yet.
Finish the 4 static gestures first, then add a separate trajectory/sequence module.
