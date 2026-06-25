// ============================================================
//  DASHBOARD  ·  Widgets cột phải, progress ring, nhật ký, toast
// ============================================================
import { HOLD_SECONDS } from './config.js';

const RING_CIRC = 2 * Math.PI * 52; // r=52 trong SVG

export class Dashboard {
  constructor() {
    this.el = {
      ringWrap:    document.getElementById('ring-wrap'),
      ringFill:    document.getElementById('ring-fill'),
      ringEmoji:   document.getElementById('ring-emoji'),
      ringLabel:   document.getElementById('ring-label'),
      statGesture: document.getElementById('stat-gesture'),
      statConf:    document.getElementById('stat-conf'),
      statHand:    document.getElementById('stat-hand'),
      statSource:  document.getElementById('stat-source'),
      fpsTag:      document.getElementById('fps-tag'),
      logList:     document.getElementById('log-list'),
      rehabFill:   document.getElementById('rehab-fill'),
      rehabCount:  document.getElementById('rehab-count'),
      clock:       document.getElementById('clock'),
      toast:       document.getElementById('toast'),
      // Session stats
      ssDuration:  document.getElementById('ss-duration'),
      ssTotal:     document.getElementById('ss-total'),
      ssTopIcon:   document.getElementById('ss-top-icon'),
      ssTopLabel:  document.getElementById('ss-top-label'),
    };
    this.el.ringFill.style.strokeDasharray  = RING_CIRC;
    this.el.ringFill.style.strokeDashoffset = RING_CIRC;

    this.rehab = 0; this.rehabMax = 10;
    // Session stats
    this._sessionStart   = Date.now();
    this._gestureCounts  = {};
    this._totalGestures  = 0;

    this._logEmpty();
    this._startClock();
    this._startSessionTimer();
  }

  // -------- Progress Ring --------
  setRing({ visible, progress = 0, emoji = '🖐️', label = '', fired = false, armed = false }) {
    const w = this.el.ringWrap;
    w.classList.toggle('show', visible);
    w.classList.toggle('fired', fired);
    w.classList.toggle('armed', armed && !fired);
    this.el.ringFill.style.strokeDashoffset = RING_CIRC * (1 - Math.min(progress, 1));
    if (emoji) this.el.ringEmoji.textContent = emoji;
    if (label) this.el.ringLabel.textContent = label;
  }
  hideRing(){
    this.el.ringWrap.classList.remove('show','fired','armed');
    this.el.ringFill.style.strokeDashoffset = RING_CIRC;
  }

  // -------- Thông số AI --------
  setStats({ gesture='—', conf='—', hands=0, source }) {
    this.el.statGesture.textContent = gesture;
    this.el.statConf.textContent    = conf;
    this.el.statHand.textContent    = hands;
    if (source) this.el.statSource.textContent = source;
  }
  setFps(v){ this.el.fpsTag.textContent = v ? `${v} FPS` : '— FPS'; }
  setSource(s){ this.el.statSource.textContent = s; }

  // -------- Nhật ký hành động --------
  _logEmpty(){ this.el.logList.innerHTML = '<li class="log-empty">Chưa có hành động nào…</li>'; }
  log(text, cls='') {
    const empty = this.el.logList.querySelector('.log-empty');
    if (empty) empty.remove();
    const t = new Date().toLocaleTimeString('vi-VN', {hour:'2-digit',minute:'2-digit',second:'2-digit'});
    const li = document.createElement('li');
    if (cls) li.className = cls;
    li.innerHTML = `<span class="log-dot"></span><span class="log-time">${t}</span><span class="log-act">${text}</span>`;
    this.el.logList.prepend(li);
    while (this.el.logList.children.length > 40) this.el.logList.lastChild.remove();
  }
  clearLog(){ this.el.logList.innerHTML=''; this._logEmpty(); }

  // -------- Phục hồi chức năng --------
  bumpRehab() {
    this.rehab = Math.min(this.rehab + 1, this.rehabMax);
    this.el.rehabCount.textContent = `${this.rehab}/${this.rehabMax} lần`;
    this.el.rehabFill.style.width  = `${(this.rehab/this.rehabMax)*100}%`;
    if (this.rehab === this.rehabMax) this.toast('🎉 Hoàn thành bài tập hôm nay!');
  }

  // -------- Toast --------
  toast(msg) {
    const t = this.el.toast;
    t.innerHTML = `<span class="t-emoji">${msg.slice(0,2)}</span><span>${msg.slice(2).trim()}</span>`;
    t.classList.add('show');
    clearTimeout(this._toastT);
    this._toastT = setTimeout(()=>t.classList.remove('show'), 2600);
  }

  // -------- Đồng hồ --------
  _startClock(){
    const tick = ()=> this.el.clock.textContent =
      new Date().toLocaleTimeString('vi-VN', {hour12:false});
    tick(); setInterval(tick, 1000);
  }

  // -------- Session stats --------
  _startSessionTimer() {
    setInterval(() => {
      const secs = Math.floor((Date.now() - this._sessionStart) / 1000);
      const m = String(Math.floor(secs / 60)).padStart(2, '0');
      const s = String(secs % 60).padStart(2, '0');
      if (this.el.ssDuration) this.el.ssDuration.textContent = `${m}:${s}`;
    }, 1000);
  }

  /** Gọi mỗi khi một cử chỉ được thực hiện */
  bumpSession(gestureId, emoji, label) {
    this._totalGestures++;
    this._gestureCounts[gestureId] = (this._gestureCounts[gestureId] || 0) + 1;
    if (this.el.ssTotal) {
      this.el.ssTotal.textContent = this._totalGestures;
      // animation pop nhỏ
      this.el.ssTotal.classList.remove('pop');
      void this.el.ssTotal.offsetWidth;
      this.el.ssTotal.classList.add('pop');
    }
    const top = Object.entries(this._gestureCounts).sort((a,b)=>b[1]-a[1])[0];
    if (top && this.el.ssTopLabel) {
      this.el.ssTopIcon.textContent  = emoji;
      this.el.ssTopLabel.textContent = label;
    }
  }
}
