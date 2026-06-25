import cv2
import numpy as np
import os
import sys
from ultralytics import YOLO

MODEL_PATH = "best.pt"
if not os.path.exists(MODEL_PATH):
    print(f"❌ Không tìm thấy model {MODEL_PATH}")
    exit()

model = YOLO(MODEL_PATH)

# Cấu hình dữ liệu
DATA_DIR = "dataset_action"
ACTIONS = {
    "v": "vay_tay",
    "c": "ve_vong_tron",
    "b": "binh_thuong"
}
SEQUENCE_LENGTH = 30

for action_name in ACTIONS.values():
    os.makedirs(os.path.join(DATA_DIR, action_name), exist_ok=True)

# Lấy đường dẫn video từ dòng lệnh
if len(sys.argv) < 2:
    print("❌ Lỗi: Bạn chưa cung cấp tên file video!")
    print("👉 Cách dùng: python src/record_from_video.py ten_video.mp4")
    exit()

video_path = sys.argv[1]
if not os.path.exists(video_path):
    print(f"❌ Không tìm thấy file video: {video_path}")
    exit()

cap = cv2.VideoCapture(video_path)
fps = cap.get(cv2.CAP_PROP_FPS)
delay = int(1000 / fps) if fps > 0 else 30 # Tốc độ phát video thực tế

is_recording = False
current_action = ""
frames_data = []
is_paused = False

print("\n" + "="*50)
print(f"🎥 ĐANG PHÁT VIDEO: {video_path}")
print("="*50)
print("Hướng dẫn:")
print(" - [SPACE]: Tạm dừng / Tiếp tục phát video")
print(" - Nhấn 'v' để ghi 1 mẫu (30 frames) cho: Vẫy tay")
print(" - Nhấn 'c' để ghi 1 mẫu (30 frames) cho: Vẽ vòng tròn")
print(" - Nhấn 'b' để ghi 1 mẫu (30 frames) cho: Bình thường")
print(" - Nhấn 'q' để thoát")
print("="*50 + "\n")

while cap.isOpened():
    if not is_paused:
        ret, frame = cap.read()
        if not ret:
            print("🎬 Đã hết video!")
            break
            
        # Thu nhỏ video nếu quá to để vừa màn hình, GIỮ NGUYÊN TỶ LỆ để không bị méo/kéo giãn
        h, w, _ = frame.shape
        max_h = 720
        max_w = 1280
        scale = min(max_w / w, max_h / h)
        if scale < 1.0:
            frame = cv2.resize(frame, (int(w * scale), int(h * scale)))
            h, w, _ = frame.shape
        
        # Dự đoán bằng YOLO
        results = model.predict(frame, imgsz=320, conf=0.1, verbose=False)
        features = np.zeros(4) 
        
        if len(results) > 0 and results[0].boxes is not None and len(results[0].boxes) > 0:
            boxes = results[0].boxes
            best_idx = int(boxes.conf.argmax().item())
            x1, y1, x2, y2 = boxes.xyxy[best_idx].tolist()
            
            cx = ((x1 + x2) / 2) / w
            cy = ((y1 + y2) / 2) / h
            bw = (x2 - x1) / w
            bh = (y2 - y1) / h
            features = np.array([cx, cy, bw, bh])
            
            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
            cv2.circle(frame, (int((x1+x2)/2), int((y1+y2)/2)), 5, (0, 0, 255), -1)

        if is_recording:
            frames_data.append(features)
            frame_count = len(frames_data)
            
            cv2.putText(frame, f"Recording '{current_action}'...", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
            cv2.putText(frame, f"Frame: {frame_count}/{SEQUENCE_LENGTH}", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
            
            if frame_count == SEQUENCE_LENGTH:
                save_dir = os.path.join(DATA_DIR, current_action)
                file_count = len(os.listdir(save_dir))
                save_path = os.path.join(save_dir, f"{current_action}_{file_count}.npy")
                np.save(save_path, np.array(frames_data))
                print(f"✅ Đã lưu mẫu {file_count} -> {save_path}")
                
                is_recording = False
                frames_data = []
                current_action = ""
                cv2.putText(frame, "SAVED!", (200, 240), cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 255, 0), 4)
        else:
            cv2.putText(frame, "Press SPACE to Pause. Press key (v, c, b) to record.", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
            y_pos = 60
            for key, act_name in ACTIONS.items():
                count = len(os.listdir(os.path.join(DATA_DIR, act_name)))
                cv2.putText(frame, f"[{key}]: {act_name} ({count} samples)", (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                y_pos += 30

        cv2.imshow("Video Player", frame)
    
    # Bắt phím
    key = cv2.waitKey(delay) & 0xFF
    if key == ord('q'):
        break
    elif key == ord(' '):
        is_paused = not is_paused # Đảo trạng thái Pause
    elif not is_recording:
        char_key = chr(key) if key < 256 else ''
        if char_key in ACTIONS:
            is_recording = True
            current_action = ACTIONS[char_key]
            frames_data = []
            is_paused = False # Tự động phát tiếp nếu đang pause
            print(f"\n🎥 Đang cắt đoạn '{current_action}'...")

cap.release()
cv2.destroyAllWindows()
