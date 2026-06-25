import cv2
import mediapipe as mp
import pandas as pd
import numpy as np
import math
import os
from sklearn.model_selection import train_test_split

# =====================================================================
# 1. CẤU HÌNH ĐƯỜNG DẪN VÀ THAM SỐ ĐẦU VÀO
# =====================================================================
VIDEO_DIR = 'data/raw_videos'
OUTPUT_DIR = 'data'

# Bản đồ ánh xạ: (Tên file video gốc, Nhãn hành động tương ứng)
VIDEO_INPUTS = [
    ('nam_tay.mp4', 'Nam_Tay'),
    ('xoe_tay.mp4', 'Xoe_Tay'),
    ('chi_ngon.mp4', 'Chi_Ngon_Tro'),
    ('binh_thuong.mp4', 'Binh_Thuong')
]

# Khởi tạo MediaPipe chuyên trách ảnh tĩnh để trích xuất chính xác nhất
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=True, 
    max_num_hands=1, 
    min_detection_confidence=0.5
)

all_data = []

print("--- HỆ THỐNG BẮT ĐẦU TRÍCH XUẤT VÀ TĂNG CƯỜNG DỮ LIỆU ĐỐI XỨNG ---")

# =====================================================================
# 2. VÒNG LẶP QUÉT VIDEO & TỰ ĐỘNG NHÂN BẢN TAY ĐỐI XỨNG (AUGMENTATION)
# =====================================================================
for video_name, label in VIDEO_INPUTS:
    video_path = os.path.join(VIDEO_DIR, video_name)
    if not os.path.exists(video_path):
        print(f"[CẢNH BÁO] Không tìm thấy video: {video_path}. Tự động bỏ qua.")
        continue
        
    print(f">> Đang xử lý: {video_path} -> Nhãn mục tiêu: [{label}]")
    cap = cv2.VideoCapture(video_path)
    
    count_original = 0
    count_augmented = 0
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb_frame)
        
        if result.multi_hand_landmarks:
            for hand_landmarks in result.multi_hand_landmarks:
                # Lấy tọa độ gốc của cổ tay (Gốc tọa độ 0.0)
                wrist_x = hand_landmarks.landmark[0].x
                wrist_y = hand_landmarks.landmark[0].y
                
                temp_coords = []
                max_distance = 0.0
                
                # Bước 1: Tính khoảng cách dịch chuyển tương đối so với cổ tay
                for lm in hand_landmarks.landmark:
                    shifted_x = lm.x - wrist_x
                    shifted_y = lm.y - wrist_y
                    temp_coords.append((shifted_x, shifted_y))
                    
                    dist = math.hypot(shifted_x, shifted_y)
                    if dist > max_distance:
                        max_distance = dist
                        
                # ---------------------------------------------------------
                # VŨ KHÍ TỐI THƯỢNG: NHÂN BẢN TỌA ĐỘ TOÁN HỌC
                # ---------------------------------------------------------
                row_original = []  # Lưu tọa độ tay phải xịn (hoặc tay gốc)
                row_flipped = []   # Lưu tọa độ ảo lật ngược trục X (giả lập tay trái)
                
                for tx, ty in temp_coords:
                    norm_x = tx / max_distance if max_distance > 0 else 0
                    norm_y = ty / max_distance if max_distance > 0 else 0
                    
                    # Tay gốc giữ nguyên
                    row_original.extend([norm_x, norm_y])
                    # Tay đối xứng: Nhân ngược trục X với -1 để tạo bàn tay đối diện hoàn hảo
                    row_flipped.extend([-norm_x, norm_y])
                    
                # Gắn nhãn cho cả 2 hành vi
                row_original.append(label)
                row_flipped.append(label)
                
                # Đẩy cả 2 vào kho tổng dữ liệu
                all_data.append(row_original)
                all_data.append(row_flipped)
                
                count_original += 1
                count_augmented += 1
                
    cap.release()
    print(f"   -> Hoàn tất: Trích xuất {count_original} khung hình gốc + Tự động tạo {count_augmented} khung hình đối xứng.")

# Kiểm tra kho dữ liệu rỗng
if len(all_data) == 0:
    print("[LỖI CHÍ MẠNG] Không thu thập được dữ liệu. Hãy kiểm tra lại file video đầu vào!")
    exit()

# =====================================================================
# 3. ĐÓNG GÓI MA TRẬN VÀ CHIA TẬP DỮ LIỆU
# =====================================================================
# Tự động tạo tiêu đề cột từ X0, Y0 đến X20, Y20
columns = []
for i in range(21):
    columns.extend([f'X{i}', f'Y{i}'])
columns.append('Label')

df = pd.DataFrame(all_data, columns=columns)

print("\n--- BẮT ĐẦU XẺ MA TRẬN VÀ XUẤT FILE CSV ---")
# Chia dữ liệu theo tỷ lệ chuẩn: Train 70% | Val 15% | Test 15% (Giữ nguyên phân phối nhãn)
train_df, test_val_df = train_test_split(df, test_size=0.30, random_state=42, stratify=df['Label'])
val_df, test_df = train_test_split(test_val_df, test_size=0.50, random_state=42, stratify=test_val_df['Label'])

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
    
train_df.to_csv(os.path.join(OUTPUT_DIR, 'train.csv'), index=False)
val_df.to_csv(os.path.join(OUTPUT_DIR, 'val.csv'), index=False)
test_df.to_csv(os.path.join(OUTPUT_DIR, 'test.csv'), index=False)

print(f"[THÀNH CÔNG] Tổng quy mô kho dữ liệu mới (Đã nhân đôi): {len(df)} mẫu số học.")
print(f"[THÀNH CÔNG] Tập Học Tập  (Train 70%): {len(train_df)} mẫu -> data/train.csv")
print(f"[THÀNH CÔNG] Tập Thi Thử  (Val   15%): {len(val_df)} mẫu -> data/val.csv")
print(f"[THÀNH CÔNG] Tập Khảo Sát (Test  15%): {len(test_df)} mẫu -> data/test.csv")
print("--- HOÀN TẤT GIAI ĐOẠN 1: DỮ LIỆU ĐÃ SẴN SÀNG CHO CẢ HAI TAY ---")