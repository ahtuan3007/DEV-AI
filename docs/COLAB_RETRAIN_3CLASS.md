# Train lai YOLO 3 class, bo bbox Binh_Thuong

Muc tieu: khong train `Binh_Thuong` nhu mot bbox class nua.

App se tu hieu:

```text
Khong co detection -> Binh_Thuong / Idle
```

## 1. File da chuan bi san

Dataset moi:

```text
D:\DEV_AI\dataset_3class
D:\DEV_AI\dataset_3class.zip
```

Notebook Colab moi:

```text
D:\DEV_AI\training\colab_train_3class.ipynb
```

Class moi:

```text
0 Nam_Tay
1 Chi_Ngon_Tro
2 Xoe_Tay
```

Anh `Binh_Thuong` van duoc giu lai lam negative/background image, nhung label `.txt` trong do de trong.

## 2. Upload len Google Drive

Upload file:

```text
D:\DEV_AI\dataset_3class.zip
```

vao:

```text
MyDrive/SmartHospital/dataset_3class.zip
```

## 3. Train tren Colab

Mo notebook:

```text
D:\DEV_AI\training\colab_train_3class.ipynb
```

Trong Colab:

```text
Runtime -> Change runtime type -> T4 GPU -> Save
```

Chay tung cell tu tren xuong duoi.

Ket qua se duoc copy ve Drive:

```text
MyDrive/SmartHospital/best_3class.pt
MyDrive/SmartHospital/best.pt
```

## 4. Sau khi train xong

Tai `best_3class.pt` ve may, doi ten thanh `best.pt` neu can, dat vao:

```text
D:\DEV_AI\best.pt
```

Sau do copy vao model app:

```powershell
cd D:\DEV_AI
Copy-Item .\best.pt .\models\best.pt -Force
.\scripts\run_terminal_test.cmd
```

## 5. Neu van nhan sai

Khong them lai class `Binh_Thuong`.

Can sua dataset theo huong:

- Anh `Nam_Tay` phai ro khac voi anh tay binh thuong.
- Anh background/binh thuong khong duoc co bbox.
- Moi class hanh dong nen co nhieu goc quay, anh sang, khoang cach.
- Neu model bao nham action khi khong lam gi, tang `--conf` hoac them background image khong label.
