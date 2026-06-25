// ============================================================
//  MotionTracker  ·  Suy ra cử chỉ ĐỘNG (vuốt / vẫy tay) từ
//  chuyển động ngang của khung nhận diện YOLOv8 theo thời gian.
//  (classifyPose bên dưới là tiện ích hình học từ landmark — giữ
//   lại để tham khảo, KHÔNG dùng trong luồng YOLOv8 hiện tại.)
// ============================================================
import { MOTION } from './config.js';

// Chỉ số landmark của MediaPipe Hands
const WRIST = 0;
const TIPS = { thumb:4, index:8, middle:12, ring:16, pinky:20 };
const PIPS = { thumb:2, index:6, middle:10, ring:14, pinky:18 };
const MCPS = { index:5, middle:9, ring:13, pinky:17 };

const dist = (a, b) => Math.hypot(a.x - b.x, a.y - b.y);

// Một ngón (trừ ngón cái) coi là "duỗi" khi đầu ngón xa cổ tay hơn khớp PIP.
function isExtended(lm, finger) {
  const w = lm[WRIST];
  return dist(lm[TIPS[finger]], w) > dist(lm[PIPS[finger]], w) * 1.05;
}

// Ngón cái: so khoảng cách ngang đầu ngón cái với khớp để biết xoè/cụp.
function thumbExtended(lm) {
  const w = lm[WRIST];
  const tip = lm[TIPS.thumb], ip = lm[PIPS.thumb];
  // xét cả khoảng cách tới cổ tay và độ tách khỏi gốc ngón trỏ
  const spread = dist(tip, lm[MCPS.index]);
  return dist(tip, w) > dist(ip, w) * 1.02 && spread > 0.08;
}

/**
 * Phân loại tư thế tĩnh từ landmark.
 * @returns {{pose:string, confidence:number, fingers:object}}
 */
export function classifyPose(lm) {
  const f = {
    thumb:  thumbExtended(lm),
    index:  isExtended(lm, 'index'),
    middle: isExtended(lm, 'middle'),
    ring:   isExtended(lm, 'ring'),
    pinky:  isExtended(lm, 'pinky'),
  };
  const four = [f.index, f.middle, f.ring, f.pinky];
  const upCount = four.filter(Boolean).length;

  let pose = 'none', confidence = 0.6;

  if (upCount === 0 && !f.thumb) {
    pose = 'fist'; confidence = 0.95;                         // ✊ Nắm tay
  } else if (f.index && !f.middle && !f.ring && !f.pinky) {
    pose = 'point'; confidence = 0.93;                        // ☝️ Chỉ ngón trỏ
  } else if (upCount >= 4) {
    pose = 'open'; confidence = f.thumb ? 0.96 : 0.88;        // 🖐️ Xòe tay
  } else if (upCount === 0 && f.thumb) {
    pose = 'fist'; confidence = 0.8;                          // nắm tay (ngón cái hơi xoè)
  } else {
    pose = 'other'; confidence = 0.5;
  }
  return { pose, confidence, fingers: f, openCount: upCount };
}

// ----------------------------------------------------------------
//  Theo dõi chuyển động ngang của cổ tay để nhận "vuốt" & "vẫy tay".
// ----------------------------------------------------------------
export class MotionTracker {
  constructor() { this.samples = []; this.lastFire = 0; }
  reset() { this.samples = []; }

  /**
   * @param {number} x  toạ độ x cổ tay (0..1, đã ở hệ ảnh hiển thị)
   * @param {number} now timestamp ms
   * @param {boolean} handOpen tay đang ở dạng xoè/phẳng (điều kiện cho vuốt/vẫy)
   * @returns {string|null}  'swipe_left' | 'swipe_right' | 'wave' | null
   */
  push(x, now, handOpen) {
    this.samples.push({ x, t: now });
    // chỉ giữ cửa sổ thời gian gần nhất
    const win = Math.max(MOTION.swipeWindowMs, MOTION.waveWindowMs);
    while (this.samples.length && now - this.samples[0].t > win) this.samples.shift();

    if (now - this.lastFire < MOTION.cooldownMs) return null;
    if (!handOpen || this.samples.length < 4) return null;

    // ----- đếm số lần đổi chiều trong cửa sổ "vẫy" -----
    const waveSamples = this.samples.filter(s => now - s.t <= MOTION.waveWindowMs);
    let reversals = 0, prevDir = 0, moved = 0;
    for (let i = 1; i < waveSamples.length; i++) {
      const dx = waveSamples[i].x - waveSamples[i-1].x;
      if (Math.abs(dx) < MOTION.minVelocity) continue;
      moved += Math.abs(dx);
      const dir = dx > 0 ? 1 : -1;
      if (prevDir !== 0 && dir !== prevDir) reversals++;
      prevDir = dir;
    }
    if (reversals >= MOTION.waveReversals && moved > MOTION.swipeDistance) {
      this.lastFire = now; this.reset(); return 'wave';        // 👋 Vẫy tay
    }

    // ----- vuốt 1 chiều trong cửa sổ "vuốt" -----
    const sw = this.samples.filter(s => now - s.t <= MOTION.swipeWindowMs);
    if (sw.length >= 3) {
      const net = sw[sw.length-1].x - sw[0].x;
      // ít đổi chiều => là vuốt chứ không phải vẫy
      let dirChanges = 0, pd = 0;
      for (let i = 1; i < sw.length; i++) {
        const dx = sw[i].x - sw[i-1].x;
        if (Math.abs(dx) < MOTION.minVelocity) continue;
        const d = dx > 0 ? 1 : -1;
        if (pd !== 0 && d !== pd) dirChanges++;
        pd = d;
      }
      if (Math.abs(net) > MOTION.swipeDistance && dirChanges <= 1) {
        this.lastFire = now; this.reset();
        // x đã ở hệ hiển thị (đã mirror): net>0 = tay sang phải màn hình
        return net > 0 ? 'swipe_right' : 'swipe_left';
      }
    }
    return null;
  }
}
