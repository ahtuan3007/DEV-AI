// ============================================================
//  YOLOv8 ENGINE  ·  Nhúng chính model best.pt (đã export ONNX)
//  Chạy offline bằng onnxruntime-web (wasm).  KHÔNG gọi internet.
//  Dùng `ort` global từ vendor/onnx/ort.min.js (nạp ở index.html).
// ============================================================
import { MotionTracker } from './gestures.js';
import { ByteTrackLite } from './tracker.js';
import { MOTION } from './config.js';

// URL tuyệt đối (theo vị trí trang) để ORT không nối nhầm thành vendor/onnx/vendor/onnx/
const MODEL_URL = new URL('models/best.onnx', document.baseURI).href;
const WASM_DIR  = new URL('vendor/onnx/', document.baseURI).href;
const INPUT = 384;   // nhỏ hơn 640 -> nhanh ~2.8x; bàn tay vẫn to rõ

// class id (theo best.pt) -> pose id của web
//   0: Nam_Tay -> fist | 1: Chi_Ngon_Tro -> point | 2: Xoe_Tay -> open
const CLASS_TO_POSE = ['fist', 'point', 'open'];
const CLASS_LABEL   = ['Nam_Tay', 'Chi_Ngon_Tro', 'Xoe_Tay'];
const NUM_CLASSES = 3;

const CONF_THRES = 0.45;   // ngưỡng tin cậy
const IOU_THRES  = 0.45;   // NMS

export class YoloEngine {
  constructor({ video, canvas, onFrame }) {
    this.video = video;
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');
    this.onFrame = onFrame;
    this.session = null;
    this.running = false;
    this.motion = new MotionTracker();
    this.tracker = new ByteTrackLite({ high: CONF_THRES, low: 0.2, iouThr: 0.2, maxLost: 12, smooth: 0.5 });
    this._raf = null;
    this._last = performance.now();
    this._fps = 0;
    this.backend = 'wasm';
    this.threads = 1;
    // canvas đệm để letterbox (INPUT x INPUT)
    this._buf = document.createElement('canvas');
    this._buf.width = this._buf.height = INPUT;
    this._bctx = this._buf.getContext('2d', { willReadFrequently: true });
    this._input = new Float32Array(3 * INPUT * INPUT);
  }

  async init(onStage) {
    if (typeof ort === 'undefined')
      throw new Error('Chưa nạp onnxruntime-web (ort.min.js).');
    onStage?.('Đang cấu hình runtime…');
    ort.env.wasm.wasmPaths = WASM_DIR;
    ort.env.wasm.simd = true;
    // Đa luồng khi trang được cô lập nguồn (COOP/COEP) -> nhanh hơn nhiều.
    // serve.py gửi sẵn header để bật; nếu không có thì tự lùi về 1 luồng.
    const isolated = (self.crossOriginIsolated === true) && (typeof SharedArrayBuffer !== 'undefined');
    this.threads = isolated ? Math.min(navigator.hardwareConcurrency || 4, 4) : 1;
    ort.env.wasm.numThreads = this.threads;
    onStage?.(`Đang nạp model YOLOv8 (${this.threads} luồng)…`);
    this.session = await ort.InferenceSession.create(MODEL_URL, {
      executionProviders: ['wasm'],
      graphOptimizationLevel: 'all',
    });
    return true;
  }

  async _openCamera() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      const e = new Error('Trình duyệt không cho camera (cần http://localhost, không mở bằng file://).');
      e.code = 'NO_API'; throw e;
    }
    try {
      return await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480, facingMode: 'user' }, audio: false });
    } catch (e) {
      const map = {
        NotAllowedError: 'Bạn đã chặn quyền camera. Bấm 🔒/📷 trên thanh địa chỉ → Cho phép → tải lại trang.',
        SecurityError:   'Bị chặn vì không phải localhost. Hãy vào đúng http://localhost:8000.',
        NotFoundError:   'Không tìm thấy webcam nào trên máy.',
        NotReadableError:'Webcam đang bị app khác chiếm (Zoom/Teams/Camera…). Đóng app đó rồi thử lại.',
      };
      const err = new Error(map[e.name] || ('Lỗi camera: ' + e.name)); err.code = e.name; throw err;
    }
  }

  async start(onStage) {
    onStage?.('Đang mở camera…');
    const stream = await this._openCamera();
    if (!this.session) {
      try { await this.init(onStage); }
      catch (e) { stream.getTracks().forEach(t=>t.stop());
        const err = new Error('Không nạp được model YOLOv8: ' + (e?.message||e)); err.code='AI_INIT'; throw err; }
    }
    this.video.srcObject = stream;
    await this.video.play();
    this.canvas.width = this.video.videoWidth || 640;
    this.canvas.height = this.video.videoHeight || 480;
    this.running = true;
    this.motion.reset();
    this._loop();
  }

  stop() {
    this.running = false;
    if (this._raf) cancelAnimationFrame(this._raf);
    const s = this.video.srcObject;
    if (s) s.getTracks().forEach(t => t.stop());
    this.video.srcObject = null;
    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
  }

  // ---- letterbox video -> tensor [1,3,640,640], trả về {r, padX, padY} ----
  _preprocess() {
    const vw = this.video.videoWidth, vh = this.video.videoHeight;
    const r = Math.min(INPUT / vw, INPUT / vh);
    const nw = Math.round(vw * r), nh = Math.round(vh * r);
    const padX = Math.floor((INPUT - nw) / 2), padY = Math.floor((INPUT - nh) / 2);
    const b = this._bctx;
    b.fillStyle = '#727272'; b.fillRect(0, 0, INPUT, INPUT);
    b.drawImage(this.video, padX, padY, nw, nh);
    const data = b.getImageData(0, 0, INPUT, INPUT).data; // RGBA
    const inp = this._input, area = INPUT * INPUT;
    for (let i = 0; i < area; i++) {
      inp[i]            = data[i*4]     / 255; // R
      inp[i + area]     = data[i*4 + 1] / 255; // G
      inp[i + area*2]   = data[i*4 + 2] / 255; // B
    }
    return { r, padX, padY, vw, vh };
  }

  // ---- giải mã output [1,7,N] + NMS -> mảng box (toạ độ video) ----
  _postprocess(out, meta) {
    const { r, padX, padY } = meta;
    const data = out.data;          // length 7*N
    const n = out.dims[2];          // số anchor (vd 3024 @384)
    const cand = [];
    for (let a = 0; a < n; a++) {
      let best = 0, bestId = 0;
      for (let c = 0; c < NUM_CLASSES; c++) {
        const s = data[(4 + c) * n + a];
        if (s > best) { best = s; bestId = c; }
      }
      if (best < CONF_THRES) continue;
      const cx = data[a], cy = data[n + a], w = data[2*n + a], h = data[3*n + a];
      // letterbox -> video coords
      const x1 = (cx - w/2 - padX) / r, y1 = (cy - h/2 - padY) / r;
      const x2 = (cx + w/2 - padX) / r, y2 = (cy + h/2 - padY) / r;
      cand.push({ x1, y1, x2, y2, score: best, cls: bestId });
    }
    return nms(cand, IOU_THRES);
  }

  _loop = () => {
    if (!this.running) return;
    const now = performance.now();

    if (this.video.readyState >= 2) {
      const meta = this._preprocess();
      const tensor = new ort.Tensor('float32', this._input, [1, 3, INPUT, INPUT]);
      this.session.run({ images: tensor }).then(res => {
        if (!this.running) return;
        const out = res.output0 || res[Object.keys(res)[0]];
        const boxes = this._postprocess(out, meta);
        this._emit(boxes, meta, performance.now());
        this._raf = requestAnimationFrame(this._loop);
      }).catch(err => {
        console.error('YOLO run error:', err);
        this._raf = requestAnimationFrame(this._loop);
      });
    } else {
      this._raf = requestAnimationFrame(this._loop);
    }
  };

  _emit(boxes, meta, now) {
    const dt = now - this._last; this._last = now;
    this._fps = this._fps * 0.85 + (1000 / dt) * 0.15;

    const frame = { handPresent:false, pose:'none', confidence:0, dynamic:null,
                    moving:false, speed:0, fps:Math.round(this._fps), threads:this.threads };

    // ByteTrack-lite: bám bàn tay qua các khung -> tâm mượt cho cử chỉ động
    const tracks = this.tracker.update(boxes);

    this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

    if (tracks.length) {
      const top = tracks.reduce((a, b) => b.score > a.score ? b : a, tracks[0]);
      frame.handPresent = true;
      frame.pose = CLASS_TO_POSE[top.cls] || 'other';
      frame.confidence = top.score;

      // vận tốc tâm tay (chuẩn hoá) từ ByteTrack -> biết tay đang ĐỘNG hay TĨNH
      frame.speed = Math.hypot(top.vx, top.vy) / meta.vw;
      frame.moving = frame.speed > MOTION.moveThreshold;

      // dùng tâm ĐÃ LÀM MƯỢT từ tracker (hệ HIỂN THỊ, đã mirror)
      const displayX = 1 - (top.cxs / meta.vw);
      frame.dynamic = this.motion.push(displayX, now, frame.pose === 'open');

      this._drawTracks(tracks, top);
    } else {
      this.motion.reset();
    }

    this.onFrame(frame);
  }

  _drawTracks(tracks, top) {
    const { ctx } = this;
    const vw = this.canvas.width;
    for (const b of tracks) {
      const isTop = b === top;
      const col = b.cls === 2 ? '#fb6f6f' : b.cls === 0 ? '#34d399' : '#60a5fa';
      // mirror sang hệ hiển thị
      const mx1 = vw - b.x2, mw = b.x2 - b.x1;
      ctx.lineWidth = isTop ? 4 : 2;
      ctx.strokeStyle = col;
      ctx.strokeRect(mx1, b.y1, mw, b.y2 - b.y1);
      // nhãn (vẽ thẳng, không mirror vì overlay không bị lật) — kèm ID track
      const txt = `#${b.id} ${CLASS_LABEL[b.cls]} ${Math.round(b.score*100)}%`;
      ctx.font = '600 16px Manrope, sans-serif';
      const tw = ctx.measureText(txt).width;
      ctx.fillStyle = col;
      ctx.fillRect(mx1, b.y1 - 22, tw + 12, 22);
      ctx.fillStyle = '#06121f';
      ctx.fillText(txt, mx1 + 6, b.y1 - 6);
    }
  }
}

// ---- Non-Maximum Suppression ----
function iou(a, b) {
  const x1 = Math.max(a.x1, b.x1), y1 = Math.max(a.y1, b.y1);
  const x2 = Math.min(a.x2, b.x2), y2 = Math.min(a.y2, b.y2);
  const w = Math.max(0, x2 - x1), h = Math.max(0, y2 - y1);
  const inter = w * h;
  const areaA = (a.x2 - a.x1) * (a.y2 - a.y1);
  const areaB = (b.x2 - b.x1) * (b.y2 - b.y1);
  return inter / (areaA + areaB - inter + 1e-6);
}
function nms(boxes, thr) {
  boxes.sort((a, b) => b.score - a.score);
  const keep = [];
  for (const b of boxes) {
    if (keep.every(k => iou(k, b) < thr)) keep.push(b);
  }
  return keep;
}
