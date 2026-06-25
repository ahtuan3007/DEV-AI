import cv2
import mediapipe as mp
import numpy as np
import math
import time
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog
from collections import deque
from datetime import datetime
import os
from ultralytics import YOLO

# =====================================================================
# 1. CẤU HÌNH HỆ THỐNG VÀ NẠP NÃO BỘ AI
# =====================================================================
MODEL_PATH = 'best.pt'

print("--- KHỞI ĐỘNG HỆ THỐNG NHẬN DIỆN (YOLOv8 - ĐỘC LẬP ÂM THANH) ---")
try:
    model = YOLO(MODEL_PATH)
    print(f"✅ Đã load model: {MODEL_PATH}")
except FileNotFoundError:
    print(f"[LỖI] Không tìm thấy {MODEL_PATH}, vui lòng kiểm tra file!")
    exit()

# ---------------------------------------------------------------------
# GIẢI PHÁP 10/10: XỬ LÝ ÂM THANH BẰNG TIẾN TRÌNH ẨN (SUBPROCESS)
# ---------------------------------------------------------------------
current_speech_process = None

def speak_async(text):
    global current_speech_process
    
    # 1. Nếu loa đang đọc câu cũ mà sếp chuyển lệnh mới -> Ép tắt loa cũ ngay lập tức
    if current_speech_process is not None and current_speech_process.poll() is None:
        current_speech_process.terminate()
        
    # 2. Tạo một kịch bản đọc lệnh siêu nhỏ gọn
    script = f"""
import pyttsx3
engine = pyttsx3.init()
engine.setProperty('rate', 160)
engine.say('{text}')
engine.runAndWait()
"""
    # 3. Kích hoạt tiến trình ẩn (Tách biệt 100% khỏi Camera, chống kẹt SAPI5 Windows)
    current_speech_process = subprocess.Popen(
        [sys.executable, "-c", script], 
        creationflags=subprocess.CREATE_NO_WINDOW
    )
# ---------------------------------------------------------------------

# Tạo tên cột chuẩn để nạp vào AI
feature_names = []
for i in range(21):
    feature_names.extend([f'X{i}', f'Y{i}'])

# Biến toàn cục bắt sự kiện quay lại Menu
go_to_menu = False

def mouse_click(event, x, y, flags, param):
    global go_to_menu
    if event == cv2.EVENT_LBUTTONDOWN:
        if 950 <= x <= 1260 and 600 <= y <= 670:
            print(">> Nhận lệnh: Đang dọn dẹp bộ nhớ để quay lại Menu...")
            go_to_menu = True

# =====================================================================
# 2. HÀM QUẢN LÝ MENU GIAO DIỆN CHUYÊN BIỆT
# =====================================================================
def show_menu():
    selected_source = [None] 

    def launch_webcam():
        selected_source[0] = 0
        root.quit()
        root.destroy()

    def launch_video():
        path = filedialog.askopenfilename(
            title="Chọn Video (.mp4) để test AI",
            filetypes=[("Video files", "*.mp4 *.mov *.avi")]
        )
        if path:
            selected_source[0] = path
        root.quit()
        root.destroy()

    def on_closing():
        root.quit()
        root.destroy()

    root = tk.Tk()
    root.title("Hệ Thống Y Tế AI - Nhóm 11")
    root.geometry("400x200")
    root.eval('tk::PlaceWindow . center')
    root.configure(bg="#2c3e50")
    root.protocol("WM_DELETE_WINDOW", on_closing) 

    tk.Label(root, text="CHỌN CHẾ ĐỘ HOẠT ĐỘNG", font=("Helvetica", 14, "bold"), fg="white", bg="#2c3e50").pack(pady=20)
    tk.Button(root, text="🎥 Chạy Camera Trực Tiếp", font=("Helvetica", 12), bg="#27ae60", fg="white", width=25, command=launch_webcam).pack(pady=10)
    tk.Button(root, text="📁 Tải Video Lên (Test)", font=("Helvetica", 12), bg="#2980b9", fg="white", width=25, command=launch_video).pack(pady=5)

    root.mainloop()
    return selected_source[0]

# =====================================================================
# 3. VÒNG LẶP TỔNG HỆ THỐNG
# =====================================================================
while True:
    source = show_menu()
    if source is None:
        print(">> Hệ thống đã đóng hoàn toàn.")
        break

    print(">> Đang kết nối nguồn cấp dữ liệu...")
    if source == 0:
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    else:
        cap = cv2.VideoCapture(source)

    window_name = "He Thong Dieu Khien Phong Benh AI"
    cv2.namedWindow(window_name)
    cv2.setMouseCallback(window_name, mouse_click)

    go_to_menu = False
    prediction_buffer = deque(maxlen=7)
    current_stable_action = "Binh_Thuong"
    last_spoken_action = "Binh_Thuong"
    last_emergency_time = 0 
    
    active_holding_action = "Binh_Thuong"
    hold_start_time = 0
    action_executed = False
    elapsed = 0

    # =====================================================================
    # 4. VÒNG LẶP XỬ LÝ HÌNH ẢNH THỜI GIAN THỰC
    # =====================================================================
    while cap.isOpened():
        if go_to_menu:
            break

        ret, frame = cap.read()
        if not ret: 
            break

        # AI QUÉT ẢNH GỐC
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb_frame)
        detected_action = "Binh_Thuong"

        if result.multi_hand_landmarks:
            for hand_landmarks in result.multi_hand_landmarks:
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                
                wrist_x = hand_landmarks.landmark[0].x
                wrist_y = hand_landmarks.landmark[0].y
                temp_coords = []
                max_distance = 0.0
                
                for lm in hand_landmarks.landmark:
                    shifted_x = lm.x - wrist_x
                    shifted_y = lm.y - wrist_y
                    temp_coords.append((shifted_x, shifted_y))
                    dist = math.hypot(shifted_x, shifted_y)
                    if dist > max_distance: max_distance = dist
                
                row_data = []
                for tx, ty in temp_coords:
                    norm_x = tx / max_distance if max_distance > 0 else 0
                    norm_y = ty / max_distance if max_distance > 0 else 0
                    row_data.extend([norm_x, norm_y])
                
                df_input = pd.DataFrame([row_data], columns=feature_names)
                detected_action = rf_model.predict(df_input)[0]

        # LẬT GƯƠNG VÀ DÀN TRANG CANVAS BẢO TOÀN TỶ LỆ
        frame = cv2.flip(frame, 1)
        canvas = np.zeros((720, 1280, 3), dtype=np.uint8)
        dash_w = 350
        cam_w = 1280 - dash_w

        h_orig, w_orig = frame.shape[:2]
        scale = 720 / h_orig
        new_w = int(w_orig * scale)
        resized_cam = cv2.resize(frame, (new_w, 720))

        if new_w >= cam_w:
            start_x = (new_w - cam_w) // 2
            canvas[:, 0:cam_w] = resized_cam[:, start_x:start_x + cam_w]
        else:
            start_x = (cam_w - new_w) // 2
            canvas[:, start_x:start_x + new_w] = resized_cam

        # BỘ LỌC ANTI-FLICKER
        prediction_buffer.append(detected_action)
        if len(prediction_buffer) == 7:
            most_common = max(set(prediction_buffer), key=prediction_buffer.count)
            if prediction_buffer.count(most_common) >= 4:
                current_stable_action = most_common

        # -----------------------------------------------------------------
        # THUẬT TOÁN ĐẾM 5 GIÂY (DWELL TIME) VÀ GỌI LOA
        # -----------------------------------------------------------------
        if current_stable_action != "Binh_Thuong":
            if current_stable_action != active_holding_action:
                active_holding_action = current_stable_action
                hold_start_time = time.time()
                action_executed = False
                elapsed = 0
            else:
                elapsed = time.time() - hold_start_time
                if elapsed >= 5.0:
                    if not action_executed:
                        action_executed = True
                        if current_stable_action == "Nam_Tay":
                            speak_async("Room light adjusted.")
                        elif current_stable_action == "Chi_Ngon_Tro":
                            speak_async("Hospital bed adjusted.")
                        elif current_stable_action == "Xoe_Tay":
                            speak_async("Emergency alert triggered.")
                            last_emergency_time = time.time()
                    else:
                        # Rú còi lặp lại nếu vẫn giữ tay Xòe
                        if current_stable_action == "Xoe_Tay":
                            if time.time() - last_emergency_time > 3.0:
                                speak_async("Emergency alert triggered.")
                                last_emergency_time = time.time()
        else:
            active_holding_action = "Binh_Thuong"
            elapsed = 0
            action_executed = False

        # -----------------------------------------------------------------
        # VẼ GIAO DIỆN DASHBOARD Y TẾ
        # -----------------------------------------------------------------
        dash_x = cam_w
        cv2.rectangle(canvas, (dash_x, 0), (1280, 720), (25, 25, 25), -1)
        
        current_time = datetime.now().strftime("%H:%M:%S")
        cv2.putText(canvas, "DASHBOARD Y TE", (dash_x + 20, 40), cv2.FONT_HERSHEY_DUPLEX, 1, (255, 255, 255), 2)
        cv2.putText(canvas, f"TIME: {current_time}", (dash_x + 20, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.line(canvas, (dash_x + 20, 90), (1260, 90), (100, 100, 100), 2)

        c_den = (80, 80, 80); c_giuong = (80, 80, 80); c_cuu = (80, 80, 80)
        blink = (0, 0, 255) if int(time.time() * 5) % 2 == 0 else (50, 50, 255)

        if action_executed:
            if current_stable_action == "Nam_Tay": c_den = (255, 191, 0)
            elif current_stable_action == "Chi_Ngon_Tro": c_giuong = (255, 50, 255)
            elif current_stable_action == "Xoe_Tay": c_cuu = blink

        cv2.rectangle(canvas, (dash_x + 20, 120), (1260, 200), c_den, -1)
        cv2.putText(canvas, "DEN PHONG", (dash_x + 80, 165), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        cv2.rectangle(canvas, (dash_x + 20, 220), (1260, 300), c_giuong, -1)
        cv2.putText(canvas, "GIUONG BENH", (dash_x + 60, 265), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        cv2.rectangle(canvas, (dash_x + 20, 320), (1260, 400), c_cuu, -1)
        cv2.putText(canvas, "BAO DONG Y TA", (dash_x + 50, 365), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        cv2.putText(canvas, f"STATUS: {current_stable_action}", (dash_x + 20, 450), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # VẼ PROGRESS BAR 5 GIÂY
        if current_stable_action != "Binh_Thuong" and not action_executed:
            pct = min(elapsed / 5.0, 1.0)
            bar_x1 = dash_x + 20
            bar_x2 = 1260
            bar_y1 = 480
            bar_y2 = 505
            
            cv2.rectangle(canvas, (bar_x1, bar_y1), (bar_x2, bar_y2), (40, 40, 40), -1)
            fill_x2 = int(bar_x1 + (bar_x2 - bar_x1) * pct)
            cv2.rectangle(canvas, (bar_x1, bar_y1), (fill_x2, bar_y2), (46, 204, 113), -1)
            
            rem_time = max(0.0, 5.0 - elapsed)
            cv2.putText(canvas, f"GIU TAY KICH HOAT SAU: {rem_time:.1f}s", (dash_x + 20, 540), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        elif action_executed:
            cv2.putText(canvas, "LENH DA DUOC THUC THI!", (dash_x + 20, 540), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # NÚT QUAY LẠI MENU
        cv2.rectangle(canvas, (dash_x + 20, 600), (1260, 670), (70, 70, 70), -1)
        cv2.putText(canvas, "QUAY LAI MENU", (dash_x + 75, 642), cv2.FONT_HERSHEY_DUPLEX, 0.7, (255, 255, 255), 2)

        cv2.putText(canvas, "DAI NAM UNIVERSITY - IT", (10, 700), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

        cv2.imshow(window_name, canvas)
        
        if cv2.waitKey(1) & 0xFF == ord('q'): 
            print(">> Đóng hệ thống bằng phím nóng Q.")
            exit()

    cap.release()
    cv2.destroyAllWindows()
    cv2.waitKey(1)