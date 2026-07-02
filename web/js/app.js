// ============================================================
//  APP  ·  Bộ điều phối trung tâm
//  3 nguồn tín hiệu  →  triggerGesture()  →  Digital Twin + Dashboard
//    1) Nút giả lập (Mock)
//    2) Camera AI trong trình duyệt (YOLOv8 ONNX, offline)
//    3) WebSocket từ backend Python (camera thật)
// ============================================================
import { GESTURES, INSTANT, HOLD_SECONDS, BUFFER_SIZE, BUFFER_MAJORITY } from './config.js';

// ----------------------------------------------------------------
//  HỆ THỐNG ĐỌC TIẾNG VIỆT (Web Speech API — 100% offline)
// ----------------------------------------------------------------
const voice = (() => {
  // Bản đồ cử chỉ → câu đọc tiếng Việt
  const SPEECH_MAP = {
    fist:        null,          // đọc động sau khi biết trạng thái đèn
    point:       null,          // đọc động sau khi biết trạng thái giường
    swipe_left:  'Kéo rèm cửa vào',
    swipe_right: 'Mở rèm cửa ra',
    open:        'Cảnh báo kắn cấp! Đang gọi cứu trợ!',
    wave:        'Đang gọi bác sĩ, vui lòng chờ',
  };

  let _lang = null;  // cache giọng tiếng Việt

  function getViVoice() {
    if (_lang) return _lang;
    const voices = window.speechSynthesis.getVoices();
    _lang = voices.find(v => v.lang.startsWith('vi')) ||
            voices.find(v => v.lang.startsWith('vi-VN')) ||
            null;
    return _lang;
  }

  function speak(text, { rate = 1.05, pitch = 1.0 } = {}) {
    if (!text || !window.speechSynthesis) return;
    window.speechSynthesis.cancel();           // huỷ câu đang nói (tránh chồng)
    const utt = new SpeechSynthesisUtterance(text);
    utt.lang  = 'vi-VN';
    utt.rate  = rate;
    utt.pitch = pitch;
    utt.volume = 1;
    const v = getViVoice();
    if (v) utt.voice = v;
    window.speechSynthesis.speak(utt);
  }

  // Khởi tạo danh sách giọng khi trình duyệt sẵn sàng
  if (window.speechSynthesis) {
    window.speechSynthesis.onvoiceschanged = () => { _lang = null; getViVoice(); };
    getViVoice();
  }

  return {
    /**
     * Gọi sau khi cử chỉ được kích hoạt.
     * @param {string} gestureId  id của cử chỉ (fist, point, open…)
     * @param {object} twin       tham chiếu DigitalTwin để biết trạng thái thực
     */
    say(gestureId, twin) {
      let text = SPEECH_MAP[gestureId];
      // Với đèn / giường: lấy trạng thái thực tế sau khi toggle
      if (gestureId === 'fist') {
        text = twin.state.light ? 'Đã bật đèn phòng' : 'Đã tắt đèn phòng';
      } else if (gestureId === 'point') {
        text = twin.state.bedUp ? 'Nâng đầu giường' : 'Hạ đầu giường';
      }
      if (text) speak(text);
    },
  };
})();

import { Dashboard } from './dashboard.js';
import { DigitalTwin } from './digital-twin.js';

const dash = new Dashboard();
const twin = new DigitalTwin();

// map model-name (Nam_Tay…) → id (fist…) cho tín hiệu từ backend
const MODEL_TO_ID = Object.fromEntries(Object.values(GESTURES).map(g => [g.model, g.id]));

// ----------------------------------------------------------------
//  THỰC THI HÀNH ĐỘNG (đích đến chung của mọi nguồn tín hiệu)
// ----------------------------------------------------------------
function executeGesture(id, { silent = false } = {}) {
  const g = GESTURES[id];
  if (!g) return;

  switch (id) {
    case 'fist': twin.toggleLight(); break;
    case 'point': twin.toggleBed(); break;
    case 'swipe_left': twin.setCurtain(false); break;
    case 'swipe_right': twin.setCurtain(true); break;
    case 'open': twin.triggerSOS(); break;
    case 'wave': twin.callDoctor(); break;
  }

  // Đọc tiếng Việt sau khi thực thi (sau switch để biết trạng thái mới)
  if (!silent && voiceEnabled) voice.say(id, twin);

  // Cập nhật card trạng thái thiết bị
  if (typeof updateDeviceCards === 'function') updateDeviceCards();

  // bài tập phục hồi: đếm khi nắm/xòe tay
  if (id === 'fist' || id === 'open') dash.bumpRehab();

  dash.log(`${g.emoji} ${g.action}`, g.logClass);
  if (!silent) dash.toast(g.toast);
  flashRingFired(g.emoji);
}

function flashRingFired(emoji) {
  dash.setRing({ visible: true, progress: 1, emoji, label: 'Đã kích hoạt!', fired: true });
  setTimeout(() => dash.hideRing(), 900);
}

// ----------------------------------------------------------------
//  1) NÚT GIẢ LẬP (MOCK)
// ----------------------------------------------------------------
document.querySelectorAll('.mock-btn').forEach(btn => {
  btn.addEventListener('click', () => executeGesture(btn.dataset.g));
});
document.getElementById('log-clear').addEventListener('click', () => dash.clearLog());

// ----------------------------------------------------------------
//  Bộ đếm GIỮ TAY 5 GIÂY (dwell) + chống nhiễu, dùng cho camera & WS
// ----------------------------------------------------------------
const stable = {
  buffer: [],
  current: 'none',     // tư thế ổn định hiện tại
  holding: 'none',     // tư thế đang được giữ để đếm giờ
  startT: 0,
  executed: false,
};

function pushStable(pose) {
  stable.buffer.push(pose);
  if (stable.buffer.length > BUFFER_SIZE) stable.buffer.shift();
  if (stable.buffer.length === BUFFER_SIZE) {
    const counts = {};
    for (const p of stable.buffer) counts[p] = (counts[p] || 0) + 1;
    const top = Object.entries(counts).sort((a, b) => b[1] - a[1])[0];
    if (top[1] >= BUFFER_MAJORITY) stable.current = top[0];
  }
}

// các tư thế tĩnh có hành động
const STATIC_IDS = { fist: 1, point: 1, open: 1 };

function updateDwell(now) {
  const cur = stable.current;
  if (cur in STATIC_IDS) {
    if (cur !== stable.holding) {            // bắt đầu giữ tư thế mới
      stable.holding = cur; stable.startT = now; stable.executed = false;
    }
    const elapsed = (now - stable.startT) / 1000;
    const g = GESTURES[cur];
    if (!stable.executed) {
      const progress = Math.min(elapsed / HOLD_SECONDS, 1);
      dash.setRing({
        visible: true, progress, emoji: g.emoji, armed: true,
        label: `Giữ ${Math.max(0, (HOLD_SECONDS - elapsed)).toFixed(1)}s`,
      });
      if (elapsed >= HOLD_SECONDS) { stable.executed = true; executeGesture(cur); }
    }
  } else {
    stable.holding = 'none'; stable.executed = false;
    if (!dash.el.ringWrap.classList.contains('fired')) dash.hideRing();
  }
}

// ----------------------------------------------------------------
//  2) CAMERA AI (YOLOv8 ONNX, offline) — nạp động để không chặn trang
// ----------------------------------------------------------------
let engine = null, camOn = false;
let currentVideoUrl = null;
const btnCam = document.getElementById('btn-cam');
const btnUploadVid = document.getElementById('btn-upload-vid');
const videoUploadInput = document.getElementById('video-upload');
const pillAI = document.getElementById('pill-ai');

function setPill(pill, mode, text) {
  const dot = pill.querySelector('.dot');
  const lbl = pill.querySelector('.pill-label');
  dot.className = 'dot ' + (mode === 'on' ? 'dot-on' : mode === 'warn' ? 'dot-warn' : 'dot-idle');
  pill.classList.toggle('is-on', mode === 'on');
  lbl.textContent = text;
}

// Hàm khởi động AI chung cho cả Camera và Video File
async function startAI(fileUrl = null) {
  if (camOn) { stopCam(); return; }
  const isVideoMode = fileUrl !== null;
  const setBtn = (txt) => {
    if (isVideoMode) {
        btnUploadVid.textContent = txt;
        btnCam.disabled = true;
    } else {
        btnCam.textContent = txt;
        btnUploadVid.disabled = true;
    }
  };
  
  setBtn('⏳ Đang khởi động…');
  if (isVideoMode) btnUploadVid.disabled = true;
  else btnCam.disabled = true;
  
  try {
    const { YoloEngine } = await import('./yolo-engine.js');
    if (!engine) engine = new YoloEngine({
      video: document.getElementById('cam'),
      canvas: document.getElementById('overlay'),
      onFrame: onAIFrame,
    });
    await engine.start((stage) => setBtn('⏳ ' + stage), fileUrl);
    camOn = true;
    document.body.classList.add('cam-live');
    
    if (isVideoMode) {
      setBtn('⏹️ Dừng Video Test');
      btnUploadVid.classList.add('is-active');
    } else {
      setBtn('⏹️ Tắt Camera AI');
      btnCam.classList.add('is-active');
    }
    
    setPill(pillAI, 'on', 'YOLOv8 chạy');
    const th = engine.threads || 1;
    dash.setSource(`YOLOv8 ×${th}L`);
    dash.log(isVideoMode ? `📁 Chạy video test — YOLOv8 (${th} luồng)` : `🎥 Bật camera — YOLOv8 (${th} luồng)`, 'lg-good');
  } catch (err) {
    console.error(err);
    setPill(pillAI, 'warn', 'AI Lỗi');
    
    // Trả lại trạng thái nút
    btnCam.textContent = '🎥 Bật Camera AI';
    btnUploadVid.textContent = '📁 Tải Video Test';
    btnCam.disabled = false;
    btnUploadVid.disabled = false;
    btnCam.classList.remove('is-active');
    btnUploadVid.classList.remove('is-active');
    
    const msg = (err && err.message) ? err.message : 'Lỗi khởi động AI.';
    dash.toast('⚠️ ' + msg.slice(0, 80));
    dash.log('⚠️ ' + msg, 'lg-sos');
    alert('LỖI AI\n\n' + msg);
  } finally {
    if (isVideoMode) btnUploadVid.disabled = false;
    else btnCam.disabled = false;
  }
}

btnCam.addEventListener('click', () => startAI(null));

if (videoUploadInput) {
    videoUploadInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) {
            if (currentVideoUrl) URL.revokeObjectURL(currentVideoUrl);
            currentVideoUrl = URL.createObjectURL(file);
            startAI(currentVideoUrl);
            e.target.value = ''; // reset
        }
    });
}

function stopCam() {
  if (engine) engine.stop();
  camOn = false;
  if (currentVideoUrl) {
      URL.revokeObjectURL(currentVideoUrl);
      currentVideoUrl = null;
  }
  document.body.classList.remove('cam-live');
  btnCam.textContent = '🎥 Bật Camera AI';
  btnUploadVid.textContent = '📁 Tải Video Test';
  btnCam.classList.remove('is-active');
  btnUploadVid.classList.remove('is-active');
  btnCam.disabled = false;
  btnUploadVid.disabled = false;
  setPill(pillAI, 'idle', 'AI Offline');
  dash.hideRing();
  dash.setStats({ gesture: '—', conf: '—', hands: 0 });
  dash.setSource('Giả lập');
  dash.setFps(0);
  stable.buffer = []; stable.current = 'none'; stable.holding = 'none';
}

function onAIFrame(frame) {
  dash.setFps(frame.fps);
  dash.setStats({
    gesture: frame.handPresent ? (frame.moving ? labelOf(frame.pose) + ' ↔' : labelOf(frame.pose)) : '—',
    conf: frame.handPresent ? Math.round(frame.confidence * 100) + '%' : '—',
    hands: frame.handPresent ? 1 : 0,
  });

  // cử chỉ ĐỘNG (vuốt/vẫy) → kích hoạt ngay
  if (frame.dynamic && GESTURES[frame.dynamic]) {
    executeGesture(frame.dynamic);
    stable.buffer = []; stable.current = 'none'; stable.holding = 'none';
    return;
  }

  // ƯU TIÊN CHUYỂN ĐỘNG: tay đang di chuyển (vuốt/vẫy dở) -> KHÔNG đếm giờ cử chỉ
  // tĩnh. Nhờ vậy xòe tay lúc kéo ngang sẽ KHÔNG bị hiểu nhầm thành SOS.
  if (frame.moving) {
    stable.buffer = []; stable.current = 'none'; stable.holding = 'none'; stable.executed = false;
    if (!dash.el.ringWrap.classList.contains('fired')) dash.hideRing();
    return;
  }

  // tư thế TĨNH (tay đứng yên) → đưa vào bộ lọc + đếm giữ
  pushStable(frame.handPresent ? frame.pose : 'none');
  updateDwell(performance.now());
}

function labelOf(pose) {
  const g = GESTURES[pose];
  if (g) return g.label;
  return pose === 'none' ? '—' : 'Khác';
}

// ----------------------------------------------------------------
//  3) NÚT BẬT/TẮT GIỌNG NÓI + CẬP NHẬT TRẠNG THÁI THIẾT BỊ
// ----------------------------------------------------------------
let voiceEnabled = true;
const btnVoice = document.getElementById('btn-voice');
const voiceStatusEl = document.getElementById('v-voice-status');

btnVoice.addEventListener('click', () => {
  voiceEnabled = !voiceEnabled;
  btnVoice.textContent = voiceEnabled ? '🔇 Tắt Giọng Nói' : '🔊 Bật Giọng Nói';
  btnVoice.classList.toggle('is-active', voiceEnabled);
  if (voiceStatusEl) voiceStatusEl.textContent = voiceEnabled ? '🔊 Đang bật' : '🔇 Đã tắt';
  dash.toast(voiceEnabled ? '🔊 Đã bật giọng nói tiếng Việt' : '🔇 Đã tắt giọng nói');
  dash.log(voiceEnabled ? '🔊 Bật giọng nói tiếng Việt' : '🔇 Tắt giọng nói', 'lg-good');
});
// Khởi tạo trạng thái nút
btnVoice.textContent = '🔇 Tắt Giọng Nói';
btnVoice.classList.add('is-active');

// Cập nhật card trạng thái thiết bị trên giao diện
const deviceCards = {
  light:   { card: document.getElementById('card-light'),   val: document.getElementById('v-light-status') },
  bed:     { card: document.getElementById('card-bed'),     val: document.getElementById('v-bed-status') },
  curtain: { card: document.getElementById('card-curtain'), val: document.getElementById('v-curtain-status') },
};

function updateDeviceCards() {
  const s = twin.state;
  if (deviceCards.light.val)   { deviceCards.light.val.textContent   = s.light       ? 'Bật'   : 'Tắt'; }
  if (deviceCards.bed.val)     { deviceCards.bed.val.textContent     = s.bedUp       ? 'Nâng'  : 'Phẳng'; }
  if (deviceCards.curtain.val) { deviceCards.curtain.val.textContent = s.curtainOpen ? 'Mở'    : 'Đóng'; }
  if (deviceCards.light.card)   deviceCards.light.card.classList.toggle('active', s.light);
  if (deviceCards.bed.card)     deviceCards.bed.card.classList.toggle('active', s.bedUp);
  if (deviceCards.curtain.card) deviceCards.curtain.card.classList.toggle('active', s.curtainOpen);
}

// Ghi đè executeGesture để cập nhật card + kiểm tra voice toggle
const _origExecute = executeGesture;
// (thêm vào sau executeGesture gốc qua event)

// Ẩn pill WS vì không còn nút backend
const pillWS = document.getElementById('pill-ws');
if (pillWS) pillWS.style.display = 'none';

// ----------------------------------------------------------------
//  Khởi động: log chào + phím tắt demo (1..6)
// ----------------------------------------------------------------
dash.log('✅ Hệ thống sẵn sàng — chọn nguồn tín hiệu hoặc bấm nút giả lập', 'lg-good');

const KEYMAP = { '1': 'fist', '2': 'point', '3': 'swipe_left', '4': 'swipe_right', '5': 'open', '6': 'wave' };
window.addEventListener('keydown', e => {
  if (KEYMAP[e.key]) executeGesture(KEYMAP[e.key]);
});

// expose để debug/console
window.HospitalRoom = { executeGesture, twin, dash, voice };
