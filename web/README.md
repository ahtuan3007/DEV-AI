# 🏥 Phòng Bệnh Thông Minh — Web Dashboard

Bảng điều khiển **Smart Hospital Room** điều khiển bằng **cử chỉ tay**, thiết kế
phong cách **Glassmorphism** y tế hiện đại, chạy **100% offline** trong trình duyệt.

Não bộ AI là **chính model YOLOv8 `best.pt` của bạn** (đã export sang ONNX), được
**nhúng thẳng vào web** và chạy bằng **onnxruntime-web (wasm)** — model & runtime
đã tải sẵn trong `models/best.onnx` + `vendor/onnx/`, không gọi internet.

---

## 🚀 Chạy nhanh

> Camera & MediaPipe bắt buộc chạy qua `http://localhost` (không mở trực tiếp file).

**Cách 1 — bấm đúp:**
```
web/start.cmd
```
**Cách 2 — PowerShell:**
```powershell
./web/start.ps1
```
**Cách 3 — thủ công:**
```powershell
cd web
python -m http.server 8000
# mở http://localhost:8000
```

---

## 🎛️ 3 nguồn tín hiệu (đều đổ về cùng một bộ điều phối)

| Nguồn | Cách dùng | Mục đích |
|---|---|---|
| **🧪 Nút giả lập (Mock)** | Bấm 6 nút ở cột giữa | Test hiệu ứng ngay, không cần camera |
| **🎥 Camera AI** | Bấm *“Bật Camera AI”* | YOLOv8 (ONNX) nhận diện tay thật ngay trong trình duyệt |
| **🔌 WebSocket** | Bấm *“Kết nối Backend”* | Cắm backend Python chạy `best.pt` — xem dưới |

⌨️ Phím tắt demo: **1** Nắm tay · **2** Chỉ trỏ · **3** Vuốt trái · **4** Vuốt phải · **5** SOS · **6** Vẫy tay.

---

## ✋ 6 cử chỉ → hiệu ứng phòng bệnh

| Cử chỉ | Class model | Hiệu ứng Digital Twin |
|---|---|---|
| ✊ Nắm tay | `Nam_Tay` | Bật/tắt đèn — nền tối ↔ sáng ấm |
| ☝️ Chỉ ngón trỏ | `Chi_Ngon_Tro` | Nâng/hạ đầu giường bệnh |
| 👈 Vuốt trái | `Vuot_Trai` | Kéo rèm cửa vào |
| 👉 Vuốt phải | `Vuot_Phai` | Mở rèm cửa ra |
| 🖐️ Xòe tay (SOS) | `Xoe_Tay` | Viền trang nhấp nháy đỏ/cam + còi quay |
| 👋 Vẫy tay | `vay_tay` | Hộp thoại “Đang gọi bác sĩ…” trên đầu giường |

> **Model `best.pt` chỉ có 3 class**: `Nam_Tay`, `Chi_Ngon_Tro`, `Xoe_Tay` (3 cử chỉ
> **tĩnh**, YOLOv8 nhận diện trực tiếp). **Vuốt** & **Vẫy tay** là cử chỉ **động**:
> web suy ra từ chuyển động ngang của bàn tay, **bám bằng ByteTrack-lite** ([tracker.js](js/tracker.js))
> để tâm tay mượt và ổn định. Vẫn có **nút giả lập** cho chắc chắn.

Cử chỉ **tĩnh** (nắm/chỉ/xòe) cần **giữ ~4 giây** (Progress Ring đếm ngược).
Cử chỉ **động** (vuốt/vẫy) kích hoạt ngay. Đổi thời gian giữ trong `js/config.js` →
`HOLD_SECONDS`.

### ⚡ Hiệu năng (đo thực tế, headless Chrome)

| Cấu hình | FPS |
|---|---|
| Cũ: wasm đơn luồng @640 | ~2 |
| Đơn luồng @384 (server thường) | ~6 |
| **Đa luồng @384 (`serve.py`)** | **~11** |

- **Input 384** thay vì 640 → nhanh ~2.8× (bàn tay vẫn to rõ).
- **Đa luồng WASM**: `serve.py` gửi header `COOP/COEP credentialless` để bật
  SharedArrayBuffer → ORT chạy 4 luồng. Dùng `python -m http.server` thì tự lùi về
  1 luồng (vẫn ~6 FPS). Số luồng hiển thị ở ô **Nguồn** (vd `YOLOv8 ×4L`).
- Nhanh hơn nữa: backend Python (`best.pt` + GPU) qua WebSocket.

---

## 🎯 Đánh giá & lưu ý về CỬ CHỈ ĐỘNG (vuốt / vẫy)

### Đánh giá thẳng thắn
Model `best.pt` **chỉ học 3 tư thế tĩnh** (`Nam_Tay`, `Chi_Ngon_Tro`, `Xoe_Tay`).
Nó **không có khái niệm thời gian / chuyển động**, nên **vuốt** và **vẫy** không phải
do model nhận — mà do web **suy luận từ quỹ đạo bàn tay**. Vì cả vuốt lẫn vẫy đều dùng
**bàn tay xòe**, mà xòe tay lại **trùng** với cử chỉ **SOS (tĩnh)**, nên có **xung đột
bản chất**: giữ xòe tay hơi lâu là dính SOS trước khi kịp kéo tay.

### Lưu ý (đã xử lý ở bản này)
- **Ưu tiên chuyển động**: khi tâm bàn tay đang di chuyển (vận tốc > `MOTION.moveThreshold`),
  web **tạm dừng & reset** đồng hồ đếm cử chỉ tĩnh. → **Đang kéo/vẫy thì SOS KHÔNG nổ.**
  SOS chỉ kích hoạt khi xòe tay **đứng yên** đủ ~4 giây. Ô “Cử chỉ” hiện thêm dấu `↔`
  khi tay đang động.
- **ByteTrack-lite** làm mượt tâm tay → vuốt/vẫy ổn định hơn ở fps vừa.
- Đã kiểm thử logic (deterministic): xòe-đứng-yên ⇒ không động (SOS được phép),
  kéo ngang ⇒ `swipe`, qua-lại ⇒ `wave`. ✅

### ⚠️ Hạn chế còn lại (phải biết khi demo)
1. **Vẫy vs Vuốt dễ lẫn**: cả hai đều là chuyển động ngang; phân biệt chỉ bằng “số lần
   đổi chiều”. Vẫy chậm/1 nhịp có thể bị tính thành vuốt và ngược lại.
2. **Phụ thuộc fps**: dưới ~6 fps thì cửa sổ thời gian thiếu mẫu → vuốt/vẫy chập chờn.
   Nên chạy bằng `serve.py` (đa luồng) hoặc backend GPU.
3. **Chỉ 1 tay**: cấu hình `numHands/numTracks = 1`; nhiều tay trong khung sẽ gây nhiễu.
4. **Không phải nhận dạng hành động thật**: đây là heuristic quỹ đạo, không phải model
   thời gian — độ chính xác kém hơn cử chỉ tĩnh.

### 🚀 Cần nâng cấp (lộ trình đề xuất)
| Mức | Việc làm | Lợi ích |
|---|---|---|
| **Nhanh** | Tách tư thế cho vuốt/vẫy (vd vuốt = **nắm tay** kéo ngang, để **xòe tay** chỉ dành cho SOS) | Xoá hẳn xung đột xòe-tay-vs-SOS |
| **Nhanh** | Tinh chỉnh `MOTION` (`moveThreshold`, `swipeDistance`, `waveReversals`, `cooldownMs`) theo camera thật | Giảm lẫn vuốt/vẫy |
| **Vừa** | Thêm **class động vào YOLO** (gán nhãn khung “đang vuốt/đang vẫy”) rồi train lại `best.pt` | Model tự nhận, bỏ heuristic |
| **Chuẩn** | Dùng **model thời gian** (LSTM/GRU/TCN) trên chuỗi landmark — dự án đã có sẵn `dataset_action/vay_tay/*.npy` | Nhận hành động đúng nghĩa, chính xác cao |
| **Tối ưu** | Đẩy nhận diện sang **backend GPU** (`backend_bridge.py`), web chỉ hiển thị | FPS cao, mượt nhất |

> 💡 Khuyến nghị cho đồ án: trước mắt **đổi vuốt sang dùng nắm tay** (hết xung đột),
> và nói rõ trong báo cáo rằng vuốt/vẫy là *heuristic quỹ đạo*; phần “nâng cấp tương lai”
> nêu hướng **LSTM trên `dataset_action`** — đúng bài, có chiều sâu.

---

## 🔌 Cắm backend Python (camera thật + best.pt)

File `backend_bridge.py` chạy chính `best.pt` (YOLOv8) trên camera bằng Python,
rồi phát cử chỉ qua WebSocket cho web (hữu ích khi muốn dùng GPU cho nhanh).

```powershell
pip install websockets ultralytics opencv-python
python web/backend_bridge.py
```
Sau đó bấm **“Kết nối Backend”** trên web. Giao thức tin nhắn rất đơn giản:
```json
{ "gesture": "Nam_Tay", "confidence": 0.94 }
```
Backend có thể gửi `id` của web (`fist`, `point`, `open`, `swipe_left`,
`swipe_right`, `wave`) hoặc tên class gốc (`Nam_Tay`…). Web tự ánh xạ.

---

## 📁 Cấu trúc

```
web/
├── index.html              # Bố cục 3 cột + SVG phòng bệnh
├── css/style.css           # Glassmorphism, animation, SOS, ring
├── js/
│   ├── app.js              # Bộ điều phối trung tâm (3 nguồn → hiệu ứng)
│   ├── config.js           # Cấu hình + bản đồ cử chỉ
│   ├── yolo-engine.js      # YOLOv8 ONNX inference (nhúng, offline, đa luồng)
│   ├── tracker.js          # ByteTrack-lite (bám tay, mượt cử chỉ động)
│   ├── gestures.js         # MotionTracker (suy ra vuốt/vẫy)
│   ├── digital-twin.js     # Điều khiển SVG phòng bệnh
│   ├── dashboard.js        # Widget cột phải, ring, log, toast
│   └── websocket-client.js # Cầu nối backend
├── models/best.onnx        # Model YOLOv8 của bạn (export từ best.pt)
├── vendor/onnx/            # onnxruntime-web (wasm) — chạy offline
├── serve.py                # Server cục bộ (ép đúng MIME .mjs/.wasm)
├── backend_bridge.py       # (tùy chọn) best.pt + GPU → web qua WebSocket
└── start.cmd / start.ps1   # Khởi động server cục bộ
```

---

## ℹ️ Cách `best.pt` được nhúng vào web

`best.pt` là model PyTorch, không chạy thẳng trong trình duyệt. Đã export sang ONNX:

```powershell
# patch tương thích torch 2.6+ rồi export (đã làm sẵn, đây là cách tái tạo)
python -c "import torch,functools; torch.load=functools.partial(torch.load,weights_only=False); torch.onnx.export=functools.partial(torch.onnx.export,dynamo=False); from ultralytics import YOLO; YOLO('best.pt').export(format='onnx',imgsz=640,opset=12,simplify=False)"
copy best.onnx web\models\best.onnx
```

Web nạp `best.onnx` bằng **onnxruntime-web**, tiền xử lý ảnh (letterbox 640), chạy
inference, giải mã output `[1,7,8400]` + NMS → ra class cử chỉ. **Đúng model của
bạn, đúng trọng số, chạy 100% offline trong trình duyệt.**

> ⚠️ Phải export bằng `dynamo=False` + `opset=12`. Bản export mặc định của torch 2.11
> bị lỗi version-conversion (op Resize) khiến onnxruntime-web abort khi nạp.
