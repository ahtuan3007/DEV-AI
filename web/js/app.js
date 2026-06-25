// ============================================================
//  APP  ·  Bộ điều phối trung tâm
//  3 nguồn tín hiệu  →  triggerGesture()  →  Digital Twin + Dashboard
//    1) Nút giả lập (Mock)
//    2) Camera AI trong trình duyệt (YOLOv8 ONNX, offline)
//    3) WebSocket từ backend Python (camera thật)
// ============================================================
import { GESTURES, INSTANT, HOLD_SECONDS, BUFFER_SIZE, BUFFER_MAJORITY } from './config.js';
import { Dashboard } from './dashboard.js';
import { DigitalTwin } from './digital-twin.js';
import { WSClient } from './websocket-client.js';
import { VoiceAnnouncer } from './voice.js';

const dash = new Dashboard();
const twin = new DigitalTwin();
const voice = new VoiceAnnouncer();

// map model-name (Nam_Tay…) → id (fist…) cho tín hiệu từ backend
const MODEL_TO_ID = Object.fromEntries(Object.values(GESTURES).map(g => [g.model, g.id]));

// ----------------------------------------------------------------
//  THỰC THI HÀNH ĐỘNG (đích đến chung của mọi nguồn tín hiệu)
// ----------------------------------------------------------------
function executeGesture(id, { silent = false } = {}) {
  const g = GESTURES[id];
  if (!g) return;

  // Lấy trạng thái TRƯỚC KHI thay đổi để nói đúng lệnh
  const stateBefore = {
    lightOn: twin.state.light,
    bedUp:   twin.state.bedUp,
    curtainOpen: twin.state.curtainOpen,
  };

  switch (id) {
    case 'fist':        twin.toggleLight(); break;
    case 'point':       twin.toggleBed(); break;
    case 'swipe_left':  twin.setCurtain(false); break;
    case 'swipe_right': twin.setCurtain(true); break;
    case 'open':        twin.triggerSOS(); break;
    case 'wave':        twin.callDoctor(); break;
  }

  // Phát âm thanh tiếng Việt
  if (!silent && g.speech) {
    const text = typeof g.speech === 'function' ? g.speech(stateBefore) : g.speech;
    voice.speak(text);
  }

  // bài tập phục hồi: đếm khi nắm/xòe tay
  if (id === 'fist' || id === 'open') dash.bumpRehab();

  // cập nhật thống kê phiên
  dash.bumpSession(id, g.emoji, g.label);

  dash.log(`${g.emoji} ${g.action}`, g.logClass);
  if (!silent) dash.toast(g.toast);
  flashRingFired(g.emoji);
}

function flashRingFired(emoji){
  dash.setRing({ visible:true, progress:1, emoji, label:'Đã kích hoạt!', fired:true });
  setTimeout(()=>dash.hideRing(), 900);
}

// ----------------------------------------------------------------
//  1) NÚT GIẢ LẬP (MOCK)
// ----------------------------------------------------------------
document.querySelectorAll('.mock-btn').forEach(btn=>{
  btn.addEventListener('click', ()=>executeGesture(btn.dataset.g));
});
document.getElementById('log-clear').addEventListener('click', ()=>dash.clearLog());

// ----------------------------------------------------------------
//  Bộ đếm GIỮ TAY (dwell) + chống nhiễu, dùng cho camera & WS
// ----------------------------------------------------------------
const stable = {
  buffer: [],
  current: 'none',
  holding: 'none',
  startT: 0,
  executed: false,
};

function pushStable(pose) {
  stable.buffer.push(pose);
  if (stable.buffer.length > BUFFER_SIZE) stable.buffer.shift();
  if (stable.buffer.length === BUFFER_SIZE) {
    const counts = {};
    for (const p of stable.buffer) counts[p] = (counts[p]||0)+1;
    const top = Object.entries(counts).sort((a,b)=>b[1]-a[1])[0];
    if (top[1] >= BUFFER_MAJORITY) stable.current = top[0];
  }
}

const STATIC_IDS = { fist:1, point:1, open:1 };

function updateDwell(now) {
  const cur = stable.current;
  if (cur in STATIC_IDS) {
    if (cur !== stable.holding) {
      stable.holding = cur; stable.startT = now; stable.executed = false;
    }
    const elapsed = (now - stable.startT) / 1000;
    const g = GESTURES[cur];
    if (!stable.executed) {
      const progress = Math.min(elapsed / HOLD_SECONDS, 1);
      dash.setRing({
        visible:true, progress, emoji:g.emoji, armed:true,
        label:`Giữ ${Math.max(0,(HOLD_SECONDS-elapsed)).toFixed(1)}s`,
      });
      if (elapsed >= HOLD_SECONDS) { stable.executed = true; executeGesture(cur); }
    }
  } else {
    stable.holding = 'none'; stable.executed = false;
    if (!dash.el.ringWrap.classList.contains('fired')) dash.hideRing();
  }
}

// ----------------------------------------------------------------
//  2) CAMERA AI (YOLOv8 ONNX, offline)
// ----------------------------------------------------------------
let engine = null, camOn = false;
const btnCam = document.getElementById('btn-cam');
const pillAI = document.getElementById('pill-ai');

function setPill(pill, mode, text){
  const dot = pill.querySelector('.dot');
  const lbl = pill.querySelector('.pill-label');
  dot.className = 'dot ' + (mode==='on'?'dot-on':mode==='warn'?'dot-warn':'dot-idle');
  pill.classList.toggle('is-on', mode==='on');
  lbl.textContent = text;
}

btnCam.addEventListener('click', async ()=>{
  if (camOn) { stopCam(); return; }
  const setBtn = (txt)=>btnCam.textContent = txt;
  setBtn('⏳ Đang khởi động…');
  btnCam.disabled = true;
  try {
    const { YoloEngine } = await import('./yolo-engine.js');
    if (!engine) engine = new YoloEngine({
      video: document.getElementById('cam'),
      canvas: document.getElementById('overlay'),
      onFrame: onAIFrame,
    });
    await engine.start((stage)=>setBtn('⏳ ' + stage));
    camOn = true;
    document.body.classList.add('cam-live');
    setBtn('⏹️ Tắt Camera AI');
    btnCam.classList.add('is-active');
    setPill(pillAI, 'on', 'YOLOv8 chạy');
    const th = engine.threads || 1;
    dash.setSource(`YOLOv8 ×${th}L`);
    dash.log(`🎥 Bật camera — YOLOv8 nhận diện trực tiếp (${th} luồng, ByteTrack)`, 'lg-good');
  } catch (err) {
    console.error(err);
    setPill(pillAI, 'warn', 'AI Lỗi');
    setBtn('🎥 Bật Camera AI');
    btnCam.classList.remove('is-active');
    const msg = (err && err.message) ? err.message : 'Không mở được camera.';
    dash.toast('⚠️ ' + msg.slice(0, 80));
    dash.log('⚠️ ' + msg, 'lg-sos');
    alert('KHÔNG BẬT ĐƯỢC CAMERA AI\n\n' + msg +
          '\n\n(Mở Console F12 để xem chi tiết kỹ thuật nếu cần.)');
  } finally {
    btnCam.disabled = false;
  }
});

function stopCam(){
  if (engine) engine.stop();
  camOn = false;
  document.body.classList.remove('cam-live');
  btnCam.textContent = '🎥 Bật Camera AI';
  btnCam.classList.remove('is-active');
  setPill(pillAI, 'idle', 'AI Offline');
  dash.hideRing();
  dash.setStats({ gesture:'—', conf:'—', hands:0 });
  dash.setSource(ws.connected ? 'WebSocket' : 'Giả lập');
  dash.setFps(0);
  stable.buffer = []; stable.current='none'; stable.holding='none';
}

function onAIFrame(frame){
  dash.setFps(frame.fps);
  dash.setStats({
    gesture: frame.handPresent ? (frame.moving ? labelOf(frame.pose)+' ↔' : labelOf(frame.pose)) : '—',
    conf: frame.handPresent ? Math.round(frame.confidence*100)+'%' : '—',
    hands: frame.handPresent ? 1 : 0,
  });

  if (frame.dynamic && GESTURES[frame.dynamic]) {
    executeGesture(frame.dynamic);
    stable.buffer = []; stable.current='none'; stable.holding='none';
    return;
  }

  if (frame.moving) {
    stable.buffer = []; stable.current='none'; stable.holding='none'; stable.executed=false;
    if (!dash.el.ringWrap.classList.contains('fired')) dash.hideRing();
    return;
  }

  pushStable(frame.handPresent ? frame.pose : 'none');
  updateDwell(performance.now());
}

function labelOf(pose){
  const g = GESTURES[pose];
  if (g) return g.label;
  return pose === 'none' ? '—' : 'Khác';
}

// ----------------------------------------------------------------
//  3) WEBSOCKET (backend Python) — ẩn khỏi UI nhưng giữ logic
// ----------------------------------------------------------------
const pillWS = document.getElementById('pill-ws');
const btnWS  = document.getElementById('btn-ws');

const ws = new WSClient({
  onStatus: (st)=>{
    if (st==='open'){
      setPill(pillWS,'on','WS Kết nối'); btnWS.textContent='🔌 Ngắt Backend'; btnWS.classList.add('is-active');
      if(!camOn) dash.setSource('WebSocket'); dash.log('🔗 Đã kết nối backend Python','lg-good');
    } else if (st==='connecting'){ setPill(pillWS,'warn','WS …'); }
    else if (st==='error'){
      setPill(pillWS,'warn','WS Lỗi'); btnWS.textContent='🔌 Kết nối Backend'; btnWS.classList.remove('is-active');
      // Không toast lỗi WS nữa — ẩn khỏi người dùng
    } else {
      setPill(pillWS,'idle','WS Ngắt'); btnWS.textContent='🔌 Kết nối Backend'; btnWS.classList.remove('is-active');
      if(!camOn) dash.setSource('Giả lập');
    }
  },
  onGesture: (msg)=>{
    const id = GESTURES[msg.gesture] ? msg.gesture : MODEL_TO_ID[msg.gesture];
    if (!id) return;
    dash.setStats({ gesture: GESTURES[id].label,
      conf: msg.confidence ? Math.round(msg.confidence*100)+'%' : '—', hands:1 });
    executeGesture(id);
  },
});

btnWS.addEventListener('click', ()=>{
  if (ws.connected) ws.disconnect();
  else ws.connect();
});

// ----------------------------------------------------------------
//  Nút toggle âm thanh 🔊 / 🔇
// ----------------------------------------------------------------
const btnVoice = document.getElementById('btn-voice');
if (btnVoice) {
  if (!voice.isSupported) {
    btnVoice.title = 'Trình duyệt không hỗ trợ Text-to-Speech';
    btnVoice.disabled = true;
  }
  btnVoice.addEventListener('click', () => {
    const on = voice.toggle();
    btnVoice.textContent = on ? '🔊' : '🔇';
    btnVoice.title = on ? 'Tắt âm thanh' : 'Bật âm thanh';
    btnVoice.classList.toggle('voice-off', !on);
    dash.toast(on ? '🔊 Âm thanh đã BẬT' : '🔇 Âm thanh đã TẮT');
  });
}

// ----------------------------------------------------------------
//  Khởi động
// ----------------------------------------------------------------
dash.log('✅ Hệ thống sẵn sàng — chọn nguồn tín hiệu hoặc bấm nút giả lập', 'lg-good');
if (voice.isSupported) {
  dash.log('🔊 Text-to-Speech sẵn sàng — sẽ đọc lệnh bằng tiếng Việt khi có cử chỉ', 'lg-good');
}

const KEYMAP = { '1':'fist','2':'point','3':'swipe_left','4':'swipe_right','5':'open','6':'wave' };
window.addEventListener('keydown', e=>{
  if (KEYMAP[e.key]) executeGesture(KEYMAP[e.key]);
});

window.HospitalRoom = { executeGesture, twin, dash, ws, voice };
