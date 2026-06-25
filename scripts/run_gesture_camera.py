from __future__ import annotations

import argparse
import collections
import time
import tkinter as tk
import sys
import subprocess
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from tkinter import filedialog
from typing import Deque, Optional, Tuple, List

import cv2
from ultralytics import YOLO


current_speech_process = None

def speak_async(text: str):
    global current_speech_process
    
    # Chống kẹt SAPI5 (Windows): Không terminate tiến trình TTS đang chạy, tránh treo engine giọng nói
    if current_speech_process is not None and current_speech_process.poll() is None:
        return
        
    # Truyền lệnh qua luồng stdin (chuẩn UTF-8) để tránh lỗi mã hóa dấu tiếng Việt trên terminal
    script = f"""
import pyttsx3
engine = pyttsx3.init()
engine.setProperty('rate', 160)
engine.say('{text}')
engine.runAndWait()
"""
    current_speech_process = subprocess.Popen(
        [sys.executable, "-"], 
        stdin=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW
    )
    current_speech_process.stdin.write(script.encode('utf-8'))
    current_speech_process.stdin.close()

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_MODEL = BASE_DIR / "best.pt"

IDLE_LABEL = "Binh_Thuong"
ACTION_LABELS = {
    "Nam_Tay": "Toggle light",
    "Chi_Ngon_Tro": "Adjust bed",
    "Xoe_Tay": "SOS",
}

LABEL_ALIASES = {
    # Internal project labels.
    "nam_tay": "Nam_Tay",
    "fist": "Nam_Tay",
    "closed_fist": "Nam_Tay",
    "a": "Nam_Tay",
    "s": "Nam_Tay",
    "chi_ngon_tro": "Chi_Ngon_Tro",
    "point": "Chi_Ngon_Tro",
    "pointing": "Chi_Ngon_Tro",
    "index": "Chi_Ngon_Tro",
    "d": "Chi_Ngon_Tro",
    "g": "Chi_Ngon_Tro",
    "l": "Chi_Ngon_Tro",
    "xoe_tay": "Xoe_Tay",
    "open_hand": "Xoe_Tay",
    "open_palm": "Xoe_Tay",
    "palm": "Xoe_Tay",
    "stop": "Xoe_Tay",
    "b": "Xoe_Tay",
    "binh_thuong": IDLE_LABEL,
    "normal": IDLE_LABEL,
    "idle": IDLE_LABEL,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run gesture detection directly with OpenCV.")
    parser.add_argument("--model", default=str(DEFAULT_MODEL), help="Path to YOLO .pt model.")
    parser.add_argument("--camera", type=int, default=0, help="Webcam index.")
    parser.add_argument("--video", type=str, default=None, help="Path to video file. If set, use video instead of webcam.")
    parser.add_argument("--conf", type=float, default=0.25, help="Detection confidence threshold.")
    parser.add_argument("--xoe-conf", type=float, default=0.25, help="Minimum confidence required for Xoe_Tay.")
    parser.add_argument("--nam-conf", type=float, default=0.35, help="Minimum confidence required for Nam_Tay.")
    parser.add_argument("--chi-conf", type=float, default=0.15, help="Minimum confidence required for Chi_Ngon_Tro.")
    parser.add_argument("--action-conf", type=float, default=0.25, help="Fallback minimum confidence required for other actions.")
    parser.add_argument("--imgsz", type=int, default=320, help="YOLO inference image size.")
    parser.add_argument("--width", type=int, default=960, help="Camera frame width.")
    parser.add_argument("--height", type=int, default=720, help="Camera frame height.")
    parser.add_argument("--camera-fps", type=float, default=30.0, help="Requested webcam FPS.")
    parser.add_argument("--infer-fps", type=float, default=1.5, help="Max YOLO inference FPS.")
    parser.add_argument("--buffer", type=int, default=3, help="Smoothing buffer size.")
    parser.add_argument("--stable-ratio", type=float, default=0.67, help="Minimum buffer majority ratio to accept a stable gesture.")
    parser.add_argument("--dwell", type=float, default=5.0, help="Seconds to hold a gesture before action.")
    parser.add_argument("--device", default=None, help="YOLO device, e.g. cpu, 0. Defaults to auto.")
    parser.add_argument("--no-mirror", action="store_true", help="Disable webcam mirror view.")
    parser.add_argument("--min-box-area", type=float, default=0.002, help="Reject boxes smaller than this frame area ratio.")
    parser.add_argument("--max-box-area", type=float, default=0.80, help="Reject boxes larger than this frame area ratio.")
    parser.add_argument("--min-aspect", type=float, default=0.25, help="Reject boxes narrower than this width/height ratio.")
    parser.add_argument("--max-aspect", type=float, default=3.5, help="Reject boxes wider than this width/height ratio.")
    return parser.parse_args()


def show_source_menu() -> Optional[str]:
    """Show a tkinter dialog to choose between Camera and Video file.
    Returns None for camera, or the video file path string."""
    selected = [None]  # None = camera, string = video path
    chosen = [False]

    def choose_camera():
        selected[0] = None
        chosen[0] = True
        root.quit()
        root.destroy()

    def choose_video():
        path = filedialog.askopenfilename(
            title="Chon Video de nhan dien cu chi tay",
            filetypes=[("Video files", "*.mp4 *.mov *.avi *.mkv")],
        )
        if path:
            selected[0] = path
            chosen[0] = True
        root.quit()
        root.destroy()

    def on_closing():
        root.quit()
        root.destroy()

    root = tk.Tk()
    root.title("Smart Hospital - Chon nguon")
    root.geometry("420x220")
    root.eval("tk::PlaceWindow . center")
    root.configure(bg="#1e293b")
    root.protocol("WM_DELETE_WINDOW", on_closing)

    tk.Label(
        root, text="CHON CHE DO HOAT DONG",
        font=("Helvetica", 14, "bold"), fg="white", bg="#1e293b",
    ).pack(pady=20)
    tk.Button(
        root, text="Camera Truc Tiep",
        font=("Helvetica", 12), bg="#22c55e", fg="white", width=28,
        command=choose_camera,
    ).pack(pady=8)
    tk.Button(
        root, text="Tai Video Len (Upload)",
        font=("Helvetica", 12), bg="#3b82f6", fg="white", width=28,
        command=choose_video,
    ).pack(pady=4)

    root.mainloop()
    if not chosen[0]:
        return "__quit__"
    return selected[0]


def open_camera(index: int, width: int, height: int, fps: float) -> cv2.VideoCapture:
    cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    cap.set(cv2.CAP_PROP_FPS, fps)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    return cap


def open_video(path: str) -> cv2.VideoCapture:
    cap = cv2.VideoCapture(path)
    return cap


def box_is_plausible(
    bbox: Tuple[int, int, int, int],
    frame_shape,
    min_area: float,
    max_area: float,
    min_aspect: float,
    max_aspect: float,
) -> bool:
    h, w = frame_shape[:2]
    x1, y1, x2, y2 = bbox
    box_w = max(1, x2 - x1)
    box_h = max(1, y2 - y1)
    area_ratio = (box_w * box_h) / float(w * h)
    aspect = box_w / float(box_h)
    return min_area <= area_ratio <= max_area and min_aspect <= aspect <= max_aspect


def normalize_label(label: str) -> str:
    return label.strip().lower().replace("-", "_").replace(" ", "_")


def model_label_to_app_label(label: str) -> Optional[str]:
    return LABEL_ALIASES.get(normalize_label(label))


def pick_best_detection(
    result,
    names,
    frame_shape,
    min_area: float,
    max_area: float,
    min_aspect: float,
    max_aspect: float,
    xoe_conf: float,
    nam_conf: float,
    chi_conf: float,
    action_conf: float,
) -> Tuple[str, float, Optional[Tuple[int, int, int, int]], str]:
    boxes = result.boxes
    if boxes is None or len(boxes) == 0:
        return IDLE_LABEL, 0.0, None, "no box"

    order = boxes.conf.argsort(descending=True).tolist()
    rejected = 0
    for idx in order:
        conf = float(boxes.conf[idx].item())
        cls_id = int(boxes.cls[idx].item())
        raw_label = str(names.get(cls_id, IDLE_LABEL))
        label = model_label_to_app_label(raw_label)
        if label is None or label == IDLE_LABEL:
            rejected += 1
            continue
        
        # Áp dụng các ngưỡng tự tin riêng biệt cho từng loại cử chỉ tay
        if label == "Xoe_Tay" and conf < xoe_conf:
            rejected += 1
            continue
        elif label == "Nam_Tay" and conf < nam_conf:
            rejected += 1
            continue
        elif label == "Chi_Ngon_Tro" and conf < chi_conf:
            rejected += 1
            continue
        elif label not in ("Xoe_Tay", "Nam_Tay", "Chi_Ngon_Tro") and conf < action_conf:
            rejected += 1
            continue
        x1, y1, x2, y2 = boxes.xyxy[idx].tolist()
        bbox = (int(x1), int(y1), int(x2), int(y2))
        if box_is_plausible(bbox, frame_shape, min_area, max_area, min_aspect, max_aspect):
            note = "" if raw_label == label else f"mapped {raw_label} -> {label}"
            return label, conf, bbox, note
        rejected += 1

    return IDLE_LABEL, 0.0, None, f"rejected {rejected} unmapped/low-conf/bad box"


def stable_label(buffer: Deque[str], min_ratio: float) -> Tuple[str, float]:
    if not buffer:
        return IDLE_LABEL, 0.0
    label, count = collections.Counter(buffer).most_common(1)[0]
    ratio = count / len(buffer)
    if label != IDLE_LABEL and ratio < min_ratio:
        return IDLE_LABEL, ratio
    return label, ratio


def detect_dynamic_gesture(buffer: Deque[Optional[Tuple[float, float]]], width: int) -> str:
    """
    Phân tích quỹ đạo (X, Y) để tìm ra cử chỉ động.
    """
    # Lọc ra các điểm tọa độ hợp lệ
    xs = [pt[0] for pt in buffer if pt is not None]
    if len(xs) < 6: return ""

    # Tính độ lệch giữa các điểm (delta x)
    dxs = [xs[i] - xs[i-1] for i in range(1, len(xs))]
    
    # Đếm số lần đảo hướng di chuyển
    threshold = width * 0.03 # Bỏ qua các rung lắc nhỏ (dưới 3% chiều rộng)
    directions = []
    for dx in dxs:
        if dx > threshold:
            if not directions or directions[-1] != 'R': directions.append('R')
        elif dx < -threshold:
            if not directions or directions[-1] != 'L': directions.append('L')
            
    # Nếu đổi hướng liên tục >= 3 lần (Ví dụ: Trái -> Phải -> Trái)
    if len(directions) >= 3:
        return "VAY TAY (Wave)"
    
    # Phát hiện Vuốt (Swipe)
    if len(xs) >= 5:
        total_dx = xs[-1] - xs[0]
        if total_dx > width * 0.25: # Vuốt một đường dài hơn 25% màn hình
            return "VUOT PHAI (Swipe Right)"
        elif total_dx < -width * 0.25:
            return "VUOT TRAI (Swipe Left)"
            
    return ""


def draw_text(frame, text: str, y: int, color=(255, 255, 255), sf: float = 1.0) -> None:
    font_scale = 0.65 * sf
    thick_bg = max(1, int(4 * sf))
    thick_fg = max(1, int(2 * sf))
    cv2.putText(frame, text, (int(16 * sf), y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 0), thick_bg)
    cv2.putText(frame, text, (int(16 * sf), y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thick_fg)


def draw_panel(frame, top_left: Tuple[int, int], bottom_right: Tuple[int, int], color=(20, 24, 32), alpha=0.72) -> None:
    overlay = frame.copy()
    cv2.rectangle(overlay, top_left, bottom_right, color, -1)
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
    cv2.rectangle(frame, top_left, bottom_right, (80, 95, 120), 1)


def label_color(label: str) -> Tuple[int, int, int]:
    if label == "Nam_Tay":
        return (52, 211, 153)
    if label == "Chi_Ngon_Tro":
        return (96, 165, 250)
    if label == "Xoe_Tay":
        return (248, 113, 113)
    return (203, 213, 225)


def draw_chip(frame, x: int, y: int, text: str, color: Tuple[int, int, int], sf: float = 1.0) -> int:
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 0.55 * sf
    thickness = max(1, int(sf))
    (text_w, text_h), _ = cv2.getTextSize(text, font, scale, thickness)
    pad_x, pad_y = int(10 * sf), int(7 * sf)
    cv2.rectangle(frame, (x, y), (x + text_w + pad_x * 2, y + text_h + pad_y * 2), color, -1)
    cv2.putText(frame, text, (x + pad_x, y + text_h + pad_y), font, scale, (12, 18, 28), thickness, cv2.LINE_AA)
    return x + text_w + pad_x * 2 + int(8 * sf)


def draw_overlay(
    frame,
    detected: str,
    stable: str,
    conf: float,
    threshold: float,
    hold_progress: float,
    last_action: str,
    fps: float,
    bbox: Optional[Tuple[int, int, int, int]],
    note: str,
    stable_ratio: float,
    dynamic_text: str = "",
) -> None:
    h, w = frame.shape[:2]
    # Scale factor: 1.0 at 960px width, scales down for narrower frames
    sf = max(0.45, min(1.0, w / 960.0))

    if bbox:
        x1, y1, x2, y2 = bbox
        color = label_color(detected)
        box_thick = max(2, int(3 * sf))
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, box_thick)
        lbl_h = int(28 * sf)
        lbl_w = int(190 * sf)
        cv2.rectangle(frame, (x1, max(0, y1 - lbl_h)), (min(w, x1 + lbl_w), y1), color, -1)
        cv2.putText(frame, f"{detected} {conf:.2f}", (x1 + 4, max(14, y1 - int(6 * sf))),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.50 * sf, (15, 23, 42), max(1, int(2 * sf)), cv2.LINE_AA)

    # Top panel - spans full frame width
    panel_h = int(132 * sf)
    m = int(10 * sf)
    draw_panel(frame, (m, m), (w - m, m + panel_h))

    title_y = m + int(26 * sf)
    draw_text(frame, "SMART HOSPITAL GESTURE", title_y, (226, 232, 240), sf)

    chip_y = m + int(38 * sf)
    cx = int(20 * sf)
    cx = draw_chip(frame, cx, chip_y, f"Det: {detected}", label_color(detected), sf)
    draw_chip(frame, cx, chip_y, f"Stb: {stable}", label_color(stable), sf)

    action_y = m + int(82 * sf)
    draw_text(frame, f"Action: {last_action}", action_y, (250, 204, 21), sf)

    status_y = m + int(108 * sf)
    draw_text(frame, f"{fps:.0f}FPS | conf {threshold:.2f} | stb {stable_ratio:.0%} | q quit", status_y, (186, 230, 253), sf)

    if note:
        note_y = m + int(134 * sf)
        draw_text(frame, note, note_y, (196, 181, 253), sf)

    # Hiển thị cử chỉ động thật to ở giữa màn hình nếu có
    if dynamic_text:
        font_scale_dyn = 1.8 * sf
        thick_dyn = max(3, int(4 * sf))
        (tw, th), _ = cv2.getTextSize(dynamic_text, cv2.FONT_HERSHEY_SIMPLEX, font_scale_dyn, thick_dyn)
        dyn_x = int((w - tw) / 2)
        dyn_y = int(h / 2)
        # Nền đen mờ
        cv2.rectangle(frame, (dyn_x - 10, dyn_y - th - 10), (dyn_x + tw + 10, dyn_y + 10), (0, 0, 0), -1)
        cv2.putText(frame, dynamic_text, (dyn_x, dyn_y), cv2.FONT_HERSHEY_SIMPLEX, font_scale_dyn, (0, 255, 255), thick_dyn, cv2.LINE_AA)

    # Bottom progress bar
    bar_h = max(8, int(16 * sf))
    bar_margin = int(34 * sf)
    panel_margin = int(50 * sf)
    bar_x = int(16 * sf)
    bar_y = h - bar_margin
    bar_w = w - bar_x * 2
    draw_panel(frame, (m, h - panel_margin), (w - m, h - m), alpha=0.58)
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (70, 80, 95), 2)
    fill_w = int(max(0.0, min(1.0, hold_progress)) * bar_w)
    if fill_w:
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + fill_w, bar_y + bar_h), label_color(stable), -1)


def run_detection(model, frame, args, conf_threshold: float) -> Tuple[str, float, Optional[Tuple[int, int, int, int]], str]:
    # Sử dụng TRACK thay vì PREDICT để kích hoạt ByteTrack
    results = model.track(
        source=frame,
        conf=conf_threshold,
        imgsz=args.imgsz,
        device=args.device,
        verbose=False,
        save=False,
        tracker="bytetrack.yaml",
        persist=True # Giữ ID liên tục giữa các frame
    )
    detected, detected_conf, bbox, note = pick_best_detection(
        results[0],
        model.names,
        frame.shape,
        args.min_box_area,
        args.max_box_area,
        args.min_aspect,
        args.max_aspect,
        args.xoe_conf,
        args.nam_conf,
        args.chi_conf,
        args.action_conf,
    )
    del results
    return detected, detected_conf, bbox, note


def main() -> int:
    args = parse_args()
    model_path = Path(args.model)
    if not model_path.exists():
        print(f"Model not found: {model_path}")
        return 1

    print(f"Loading model: {model_path}")
    model = YOLO(str(model_path))
    print(f"Model classes: {model.names}")


    # Determine video source: CLI --video, or show menu
    video_path: Optional[str] = args.video
    use_video = False
    if video_path is None:
        # No --video flag: show menu to let user choose
        menu_result = show_source_menu()
        if menu_result == "__quit__":
            print("User closed the menu. Exiting.")
            return 0
        if menu_result is not None:
            video_path = menu_result
            use_video = True
    else:
        use_video = True

    display_w, display_h = args.width, args.height

    if use_video:
        if not Path(video_path).exists():
            print(f"Video not found: {video_path}")
            return 1
        cap = open_video(video_path)
        if not cap.isOpened():
            print(f"Cannot open video: {video_path}")
            return 1
        video_fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        # Calculate display size preserving aspect ratio
        vid_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        vid_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if vid_w > 0 and vid_h > 0:
            scale_fit = min(args.width / vid_w, args.height / vid_h)
            display_w = int(vid_w * scale_fit)
            display_h = int(vid_h * scale_fit)
        print(f"Video source: {video_path}")
        print(f"Video FPS: {video_fps:.1f} | Total frames: {total_frames}")
        print(f"Video original: {vid_w}x{vid_h} -> Display: {display_w}x{display_h}")
        # For video: don't mirror
        args.no_mirror = True
    else:
        cap = open_camera(args.camera, args.width, args.height, args.camera_fps)
        if not cap.isOpened():
            print(f"Cannot open webcam index {args.camera}")
            return 1
        video_fps = 0.0
        actual_fps = cap.get(cv2.CAP_PROP_FPS)
        print(f"Camera requested: {args.width}x{args.height} @ {args.camera_fps:.0f} FPS")
        if actual_fps:
            print(f"Camera reported FPS: {actual_fps:.1f}")

    labels: Deque[str] = collections.deque(maxlen=args.buffer)
    dynamic_buffer: Deque[Optional[Tuple[float, float]]] = collections.deque(maxlen=15) # Lưu 15 tọa độ gần nhất
    dynamic_display_text = ""
    dynamic_display_until = 0.0

    conf_threshold = min(args.conf, args.xoe_conf, args.nam_conf, args.chi_conf)
    infer_interval = 1.0 / max(args.infer_fps, 0.1)
    if use_video:
        infer_interval = 0  # Analyze every frame for video (no throttle)
        # Trên CPU, chạy imgsz=640 rất chậm. Ta hạ xuống 320 để xử lý cực nhanh,
        # trong khi video hiển thị trên màn hình vẫn giữ nguyên độ nét gốc.
        if args.imgsz > 320:
            print(f"Lưu ý: Đã hạ độ phân giải AI từ {args.imgsz} xuống 320 để video chạy mượt trên CPU (Video hiển thị vẫn nét).")
            args.imgsz = 320
    last_infer_at = 0.0
    last_fps_at = time.monotonic()
    frame_count = 0
    fps = 0.0

    detected = IDLE_LABEL
    detected_conf = 0.0
    bbox = None
    note = ""
    current_hold = IDLE_LABEL
    hold_started_at: Optional[float] = None
    triggered_for_hold = False
    last_action = "Idle"
    executor = ThreadPoolExecutor(max_workers=1)
    pending_detection: Optional[Future] = None

    # For video playback, calculate delay between frames to match original FPS
    frame_delay_ms = int(1000.0 / video_fps) if use_video and video_fps > 0 else 1

    window_title = "Smart Hospital - Video" if use_video else "Gesture Camera - Terminal"
    try:
        cv2.namedWindow(window_title, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_title, display_w, display_h)
        while True:
            ok, frame = cap.read()
            if not ok or frame is None:
                if use_video:
                    print("Video ended.")
                    break
                print("Cannot read frame from webcam")
                time.sleep(0.05)
                continue
            # Resize video frames to display size (preserves aspect ratio)
            if use_video:
                frame = cv2.resize(frame, (display_w, display_h))
            if not args.no_mirror:
                frame = cv2.flip(frame, 1)

            now = time.monotonic()
            # Chạy bất đồng bộ (asynchronous) để giữ luồng video/camera mượt mà 100% (30 FPS)
            # AI sẽ tự chạy song song trong luồng phụ (ThreadPoolExecutor) không gây nghẽn luồng hiển thị.
            # Do độ phân giải AI được tối ưu ở mức 320, thời gian suy luận trên CPU chỉ khoảng ~30ms (lệch tối đa 1 khung hình),
            # giúp hộp nhận diện bám sát tay gần như tức thời mà không gây khựng hình.
            if pending_detection is not None and pending_detection.done():
                try:
                    detected, detected_conf, bbox, note = pending_detection.result()
                    
                    # === XỬ LÝ CỬ CHỈ ĐỘNG ===
                    if bbox:
                        cx = (bbox[0] + bbox[2]) / 2.0
                        cy = (bbox[1] + bbox[3]) / 2.0
                        dynamic_buffer.append((cx, cy))
                    else:
                        dynamic_buffer.append(None)
                        
                    dyn_act = detect_dynamic_gesture(dynamic_buffer, display_w)
                    if dyn_act:
                        dynamic_display_text = dyn_act
                        dynamic_display_until = now + 1.5 # Hiển thị chữ trên màn hình 1.5 giây
                        dynamic_buffer.clear() # Xóa buffer để không nhận diện lặp lại
                        if "VUOT PHAI" in dyn_act:
                            speak_async("Mở rèm")
                        elif "VUOT TRAI" in dyn_act:
                            speak_async("Đóng rèm")
                        elif "VAY TAY" in dyn_act:
                            speak_async("Gọi bác sĩ")
                    # =========================
                    
                    labels.append(detected)
                except Exception as exc:
                    detected, detected_conf, bbox, note = IDLE_LABEL, 0.0, None, f"inference error: {exc}"
                    labels.append(IDLE_LABEL)
                pending_detection = None

            if pending_detection is None and now - last_infer_at >= infer_interval:
                last_infer_at = now
                pending_detection = executor.submit(run_detection, model, frame.copy(), args, conf_threshold)

            stable, stable_ratio = stable_label(labels, args.stable_ratio)
            if stable == IDLE_LABEL:
                current_hold = IDLE_LABEL
                hold_started_at = None
                triggered_for_hold = False
                hold_progress = 0.0
            else:
                if stable != current_hold:
                    current_hold = stable
                    hold_started_at = now
                    triggered_for_hold = False

                elapsed = now - hold_started_at if hold_started_at is not None else 0.0
                hold_progress = elapsed / max(args.dwell, 0.1)
                if elapsed >= args.dwell and not triggered_for_hold:
                    triggered_for_hold = True
                    last_action = ACTION_LABELS.get(stable, stable)
                    print(f"Action: {last_action} ({stable}, conf={detected_conf:.2f})")
                    if stable == "Nam_Tay":
                        speak_async("Đã điều chỉnh đèn")
                    elif stable == "Chi_Ngon_Tro":
                        speak_async("Đã điều chỉnh giường")
                    elif stable == "Xoe_Tay":
                        speak_async("Báo động y tá")
                    else:
                        speak_async(last_action)

            frame_count += 1
            if now - last_fps_at >= 1.0:
                fps = frame_count / (now - last_fps_at)
                frame_count = 0
                last_fps_at = now
            
            if now > dynamic_display_until:
                dynamic_display_text = ""

            draw_overlay(frame, detected, stable, detected_conf, conf_threshold, hold_progress, last_action, fps, bbox, note, stable_ratio, dynamic_display_text)
            cv2.imshow(window_title, frame)

            wait_ms = frame_delay_ms if use_video else 1
            key = cv2.waitKey(wait_ms) & 0xFF
            if key == ord("q") or key == 27:
                break
            if key in (ord("+"), ord("=")):
                conf_threshold = min(0.95, conf_threshold + 0.05)
                print(f"conf={conf_threshold:.2f}")
            elif key in (ord("-"), ord("_")):
                conf_threshold = max(0.05, conf_threshold - 0.05)
                print(f"conf={conf_threshold:.2f}")
            elif key == ord(" ") and use_video:
                # Space to pause/resume video
                cv2.waitKey(0)
    finally:
        executor.shutdown(wait=False, cancel_futures=True)
        cap.release()
        cv2.destroyAllWindows()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
