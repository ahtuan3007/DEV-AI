// ============================================================
//  CẤU HÌNH HỆ THỐNG  ·  Smart Hospital Room
// ============================================================

// Thời gian giữ tay để kích hoạt lệnh tĩnh (giây) — đồng bộ Progress Ring.
// (App gốc dùng 5s. Giảm còn 2–3s nếu muốn demo nhanh hơn.)
export const HOLD_SECONDS = 4;

// Bộ lọc chống nhiễu (anti-flicker) — cần >= MAJORITY khung giống nhau.
// YOLOv8 wasm ~2 FPS nên để bộ đệm nhỏ cho phản hồi nhanh (gốc 7/4 hợp 30 FPS).
export const BUFFER_SIZE = 4;
export const BUFFER_MAJORITY = 3;

// Ngưỡng nhận diện chuyển động (toạ độ chuẩn hoá 0..1 theo chiều ngang khung hình)
export const MOTION = {
  swipeDistance: 0.16,   // tổng dịch chuyển ngang để coi là "vuốt" (dễ hơn)
  swipeWindowMs: 800,    // cửa sổ thời gian theo dõi vuốt
  waveReversals: 3,      // số lần đổi chiều để coi là "vẫy tay"
  waveWindowMs: 1400,
  minVelocity: 0.0008, // ngưỡng vận tốc tối thiểu để tính 1 mẫu chuyển động
  cooldownMs: 1200,   // nghỉ giữa 2 lần kích hoạt cử chỉ động
  // Vận tốc tâm tay (chuẩn hoá theo bề ngang / khung) ở trên ngưỡng này coi là
  // "đang di chuyển" -> TẠM DỪNG đếm giờ cử chỉ tĩnh (tránh xòe tay = SOS khi vuốt/vẫy).
  moveThreshold: 0.010,
};

// WebSocket tới backend Python AI (để sau này cắm vào). Mặc định localhost.
export const WS_URL = 'ws://localhost:8765';

// ----------------------------------------------------------------
//  Bản đồ cử chỉ → hành động.  id khớp với output của classifier
//  và với class của model gốc (Nam_Tay / Chi_Ngon_Tro / Xoe_Tay / vay_tay).
// ----------------------------------------------------------------
export const GESTURES = {
  fist: {
    id: 'fist', model: 'Nam_Tay', emoji: '✊', label: 'Nắm tay',
    action: 'Bật / Tắt đèn phòng', type: 'static',
    toast: '💡 Đã điều chỉnh ánh sáng phòng', logClass: 'lg-good',
  },
  point: {
    id: 'point', model: 'Chi_Ngon_Tro', emoji: '☝️', label: 'Chỉ ngón trỏ',
    action: 'Nâng / Hạ đầu giường', type: 'static',
    toast: '🛏️ Đã điều chỉnh đầu giường', logClass: '',
  },
  open: {
    id: 'open', model: 'Xoe_Tay', emoji: '🖐️', label: 'Xòe tay (SOS)',
    action: 'Báo động khẩn cấp', type: 'static',
    toast: '🚨 KÍCH HOẠT BÁO ĐỘNG SOS', logClass: 'lg-sos',
  },
  swipe_left: {
    id: 'swipe_left', model: 'Vuot_Trai', emoji: '👈', label: 'Vuốt trái',
    action: 'Kéo rèm cửa vào', type: 'dynamic',
    toast: '🪟 Đang kéo rèm cửa', logClass: '',
  },
  swipe_right: {
    id: 'swipe_right', model: 'Vuot_Phai', emoji: '👉', label: 'Vuốt phải',
    action: 'Mở rèm cửa ra', type: 'dynamic',
    toast: '🪟 Đang mở rèm cửa', logClass: '',
  },
  wave: {
    id: 'wave', model: 'vay_tay', emoji: '👋', label: 'Vẫy tay',
    action: 'Gọi bác sĩ', type: 'dynamic',
    toast: '🩺 Đang gọi bác sĩ tới phòng', logClass: '',
  },
};

// Cử chỉ động kích hoạt ngay (không cần giữ 5s)
export const INSTANT = new Set(['swipe_left', 'swipe_right', 'wave']);
