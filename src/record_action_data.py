import cv2
import numpy as np
import os
import time
from ultralytics import YOLO

# Tải model YOLO hiện tại của bạn
MODEL_PATH = "best.pt"
if not os.path.exists(MODEL_PATH):
    print(f"❌ Không tìm thấy model {MODEL_PATH} ở thư mục hiện tại. Hãy chạy code ở D:\\DEV_AI")
    exit()

model = YOLO(MODEL_PATH)

# Cấu hình dữ liệu
DATA_DIR = "dataset_action"
ACTIONS = {
    "v": "vay_tay",         # Nhấn 'v' để quay hành động "vẫy tay"
    "c": "ve_vong_tron",    # Nhấn 'c' để quay hành động "vẽ vòng tròn" (circle)
    "b": "binh_thuong"      # Nhấn 'b' để quay lớp "bình thường" (nhiễu)
}
SEQUENCE_LENGTH = 30 # Độ dài mỗi chuỗi (30 frames ~ 1 giây)

# Tạo thư mục nếu chưa có
for action_name in ACTIONS.values():
    os.makedirs(os.path.join(DATA_DIR, action_name), exist_ok=True)

# Trạng thái ghi hình
is_recording = False
current_action = ""
frames_data = []

cap = cv2.VideoCapture(0)
print("\n" + "="*50)
print("🎥 BẮT ĐẦU THU THẬP DỮ LIỆU CỬ CHỈ ĐỘNG BẰNG YOLO")
print("="*50)
print("Hướng dẫn:")
print(" - Nhấn 'v' để ghi 1 mẫu (30 frames) cho: Vẫy tay")
print(" - Nhấn 'c' để ghi 1 mẫu (30 frames) cho: Vẽ vòng tròn")
print(" - Nhấn 'b' để ghi 1 mẫu (30 frames) cho: Bình thường (Nhiễu)")
print(" - Nhấn 'q' để thoát")
print("="*50 + "\n")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
        
    frame = cv2.flip(frame, 1) # Lật gương để dễ nhìn
    h, w, _ = frame.shape
    
    # Dự đoán bằng YOLO (giảm conf xuống tận 0.08 vì camera mờ làm mất ngón trỏ)
    results = model.predict(frame, imgsz=320, conf=0.08, verbose=False)
    
    # Trích xuất đặc trưng: (cx, cy, bw, bh) chuẩn hóa
    features = np.zeros(4) 
    
    if len(results) > 0 and results[0].boxes is not None and len(results[0].boxes) > 0:
        # Lấy box có độ tin cậy cao nhất
        boxes = results[0].boxes
        best_idx = int(boxes.conf.argmax().item())
        x1, y1, x2, y2 = boxes.xyxy[best_idx].tolist()
        
        # Tính tâm và kích thước chuẩn hóa [0, 1]
        cx = ((x1 + x2) / 2) / w
        cy = ((y1 + y2) / 2) / h
        bw = (x2 - x1) / w
        bh = (y2 - y1) / h
        features = np.array([cx, cy, bw, bh])
        
        # Vẽ box lên hình để nhìn
        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
        cv2.circle(frame, (int((x1+x2)/2), int((y1+y2)/2)), 5, (0, 0, 255), -1)

    # Xử lý khi đang quay
    if is_recording:
        frames_data.append(features)
        frame_count = len(frames_data)
        
        # Vẽ thông báo đang quay
        cv2.putText(frame, f"Recording '{current_action}'...", (10, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        cv2.putText(frame, f"Frame: {frame_count}/{SEQUENCE_LENGTH}", (10, 90), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        # Vẽ thanh tiến trình
        progress = int((frame_count / SEQUENCE_LENGTH) * 400)
        cv2.rectangle(frame, (10, 110), (10 + progress, 130), (0, 255, 0), -1)
        cv2.rectangle(frame, (10, 110), (410, 130), (255, 255, 255), 2)
        
        if frame_count == SEQUENCE_LENGTH:
            # Lưu lại dữ liệu thành file numpy
            save_dir = os.path.join(DATA_DIR, current_action)
            file_count = len(os.listdir(save_dir))
            save_path = os.path.join(save_dir, f"{current_action}_{file_count}.npy")
            
            np.save(save_path, np.array(frames_data))
            print(f"✅ Đã lưu mẫu thứ {file_count} cho hành động '{current_action}' tại {save_path}")
            
            # Reset trạng thái
            is_recording = False
            frames_data = []
            current_action = ""
            cv2.putText(frame, "SAVED!", (200, 240), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)
            cv2.imshow("Record Data", frame)
            cv2.waitKey(500)
            
    else:
        y_pos = 50
        cv2.putText(frame, "READY! Press key to record.", (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)
        for key, act_name in ACTIONS.items():
            dir_path = os.path.join(DATA_DIR, act_name)
            count = len(os.listdir(dir_path))
            cv2.putText(frame, f"[{key}]: {act_name} ({count} samples)", (10, y_pos), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            y_pos += 30

    cv2.imshow("Record Data", frame)
    
    # Bắt phím
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif not is_recording:
        char_key = chr(key) if key < 256 else ''
        if char_key in ACTIONS:
            is_recording = True
            current_action = ACTIONS[char_key]
            frames_data = []
            print(f"\n🎥 Bắt đầu quay '{current_action}'...")

cap.release()
cv2.destroyAllWindows()
