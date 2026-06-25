# ============================================================
#  BACKEND BRIDGE (tùy chọn)
#  Cầu nối: Camera thật + YOLOv8 (best.pt)  ->  Web Dashboard
#  ------------------------------------------------------------
#  Chạy chính model best.pt của bạn để nhận diện cử chỉ, rồi PHÁT
#  (broadcast) qua WebSocket cho trang web. Web tự map tên class
#  (Nam_Tay, Chi_Ngon_Tro, Xoe_Tay) -> hiệu ứng phòng bệnh.
#
#  Lưu ý: trang web ĐÃ nhúng sẵn YOLOv8 (ONNX) chạy offline trong
#  trình duyệt — bridge này chỉ cần khi bạn muốn dùng môi trường
#  Python/CUDA cho tốc độ cao hơn.
#
#  CÀI ĐẶT:
#     pip install websockets ultralytics opencv-python
#  CHẠY:
#     python web/backend_bridge.py
#  Rồi bấm "Kết nối Backend" trên web (ws://localhost:8765).
# ============================================================
import asyncio, json, threading, time, os, functools
from collections import deque

import cv2
import torch
import websockets

# --- vá tương thích torch 2.6+ (best.pt là của bạn nên tin cậy) ---
torch.load = functools.partial(torch.load, weights_only=False)
from ultralytics import YOLO

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MODEL_PATH = os.path.join(ROOT, "best.pt")
HOST, PORT = "localhost", 8765
HOLD_SECONDS = 4.0          # khớp với web (config.js)
CONF = 0.45

model = YOLO(MODEL_PATH)
NAMES = model.names         # {0:'Nam_Tay',1:'Chi_Ngon_Tro',2:'Xoe_Tay'}
print(f"[OK] Da nap YOLOv8: {MODEL_PATH}  classes={NAMES}")

clients = set()
_loop = None


def broadcast(payload: dict):
    if not clients or _loop is None:
        return
    msg = json.dumps(payload)
    for ws in list(clients):
        asyncio.run_coroutine_threadsafe(ws.send(msg), _loop)


def cv_worker():
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    buf = deque(maxlen=4)
    stable = "Binh_Thuong"
    holding = "Binh_Thuong"
    start_t = 0.0
    executed = False
    print(f"[OK] Camera bridge chay. Cho web ket noi ws://{HOST}:{PORT}")

    while True:
        ok, frame = cap.read()
        if not ok:
            time.sleep(0.05); continue

        # YOLOv8 suy luan
        res = model.predict(frame, conf=CONF, verbose=False)[0]
        detected = "Binh_Thuong"
        if len(res.boxes) > 0:
            # lay box diem cao nhat
            i = int(res.boxes.conf.argmax())
            detected = NAMES[int(res.boxes.cls[i])]

        buf.append(detected)
        if len(buf) == buf.maxlen:
            top = max(set(buf), key=buf.count)
            if buf.count(top) >= 3:
                stable = top

        now = time.time()
        if stable != "Binh_Thuong":
            if stable != holding:
                holding, start_t, executed = stable, now, False
            elapsed = now - start_t
            broadcast({"type": "progress", "gesture": stable,
                       "progress": min(elapsed / HOLD_SECONDS, 1.0)})
            if elapsed >= HOLD_SECONDS and not executed:
                executed = True
                broadcast({"gesture": stable, "confidence": 0.95})
                print(f"  -> KICH HOAT: {stable}")
        else:
            holding, executed = "Binh_Thuong", False

        cv2.putText(frame, stable, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow("YOLOv8 Bridge (q de thoat)", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    cap.release(); cv2.destroyAllWindows()


async def handler(ws):
    clients.add(ws)
    print(f"[WS] Web ket noi ({len(clients)})")
    try:
        await ws.wait_closed()
    finally:
        clients.discard(ws)
        print(f"[WS] Web ngat ({len(clients)})")


async def main():
    global _loop
    _loop = asyncio.get_running_loop()
    threading.Thread(target=cv_worker, daemon=True).start()
    async with websockets.serve(handler, HOST, PORT):
        print(f"[OK] WebSocket: ws://{HOST}:{PORT}")
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nDa dung bridge.")
