// ============================================================
//  CẤU HÌNH HỆ THỐNG  ·  Smart Hospital Room
// ============================================================

// Thời gian giữ tay để kích hoạt lệnh tĩnh (giây) — đồng bộ Progress Ring.
export const HOLD_SECONDS = 4;

// Bộ lọc chống nhiễu (anti-flicker) — giảm 4→3 để phản hồi nhanh hơn.
export const BUFFER_SIZE = 3;
export const BUFFER_MAJORITY = 2;

// Ngưỡng nhận diện chuyển động (toạ độ chuẩn hoá 0..1 theo chiều ngang khung hình)
export const MOTION = {
  swipeDistance: 0.16,
  swipeWindowMs: 800,
  waveReversals: 3,
  waveWindowMs:  1400,
  minVelocity:   0.0008,
  cooldownMs:    1200,
  moveThreshold: 0.010,
};

// WebSocket tới backend Python AI (để sau này cắm vào). Mặc định localhost.
export const WS_URL = 'ws://localhost:8765';

// ----------------------------------------------------------------
//  Bản đồ cử chỉ → hành động.
// ----------------------------------------------------------------
export const GESTURES = {
  fist: {
    id:'fist', model:'Nam_Tay', emoji:'✊', label:'Nắm tay',
    action:'Bật / Tắt đèn phòng', type:'static',
    toast:'💡 Đã điều chỉnh ánh sáng phòng', logClass:'lg-good',
    speech: (state) => state.lightOn ? 'Tắt đèn' : 'Bật đèn',
  },
  point: {
    id:'point', model:'Chi_Ngon_Tro', emoji:'☝️', label:'Chỉ ngón trỏ',
    action:'Nâng / Hạ đầu giường', type:'static',
    toast:'🛏️ Đã điều chỉnh đầu giường', logClass:'',
    speech: (state) => state.bedUp ? 'Hạ đầu giường' : 'Nâng đầu giường',
  },
  open: {
    id:'open', model:'Xoe_Tay', emoji:'🖐️', label:'Xòe tay (SOS)',
    action:'Báo động khẩn cấp', type:'static',
    toast:'🚨 KÍCH HOẠT BÁO ĐỘNG SOS', logClass:'lg-sos',
    speech: () => 'Kích hoạt báo động khẩn cấp',
  },
  swipe_left: {
    id:'swipe_left', model:'Vuot_Trai', emoji:'👈', label:'Vuốt trái',
    action:'Kéo rèm cửa vào', type:'dynamic',
    toast:'🪟 Đang kéo rèm cửa', logClass:'',
    speech: () => 'Đóng rèm cửa',
  },
  swipe_right: {
    id:'swipe_right', model:'Vuot_Phai', emoji:'👉', label:'Vuốt phải',
    action:'Mở rèm cửa ra', type:'dynamic',
    toast:'🪟 Đang mở rèm cửa', logClass:'',
    speech: () => 'Mở rèm cửa',
  },
  wave: {
    id:'wave', model:'vay_tay', emoji:'👋', label:'Vẫy tay',
    action:'Gọi bác sĩ', type:'dynamic',
    toast:'🩺 Đang gọi bác sĩ tới phòng', logClass:'',
    speech: () => 'Đang gọi bác sĩ',
  },
};

// Cử chỉ động kích hoạt ngay (không cần giữ)
export const INSTANT = new Set(['swipe_left','swipe_right','wave']);
