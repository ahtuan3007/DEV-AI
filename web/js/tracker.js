// ============================================================
//  ByteTrack-lite  ·  Bám đối tượng (bàn tay) qua các khung
//  ------------------------------------------------------------
//  Rút gọn tinh thần ByteTrack: ghép detection với track bằng IoU
//  theo 2 mức điểm (cao trước, thấp sau), giữ track khi mất tạm
//  thời, và làm MƯỢT tâm bàn tay bằng vận tốc — giúp nhận diện
//  cử chỉ ĐỘNG (vuốt/vẫy) ổn định ở fps vừa phải.
// ============================================================

function iou(a, b) {
  const x1 = Math.max(a.x1, b.x1), y1 = Math.max(a.y1, b.y1);
  const x2 = Math.min(a.x2, b.x2), y2 = Math.min(a.y2, b.y2);
  const w = Math.max(0, x2 - x1), h = Math.max(0, y2 - y1), inter = w * h;
  const ar = (a.x2-a.x1)*(a.y2-a.y1) + (b.x2-b.x1)*(b.y2-b.y1) - inter;
  return ar <= 0 ? 0 : inter / ar;
}
const cx = b => (b.x1 + b.x2) / 2;
const cy = b => (b.y1 + b.y2) / 2;

export class ByteTrackLite {
  /**
   * @param {object} o
   * @param {number} o.high   ngưỡng điểm cao (detection chắc chắn)
   * @param {number} o.low    ngưỡng điểm thấp (cứu track đang mất)
   * @param {number} o.iouThr ngưỡng IoU để ghép
   * @param {number} o.maxLost số khung tối đa giữ track khi mất
   * @param {number} o.smooth hệ số làm mượt tâm (0..1, càng nhỏ càng mượt)
   */
  constructor(o = {}) {
    this.high = o.high ?? 0.45;
    this.low = o.low ?? 0.2;
    this.iouThr = o.iouThr ?? 0.2;
    this.maxLost = o.maxLost ?? 12;
    this.smooth = o.smooth ?? 0.5;
    this.tracks = [];
    this._id = 0;
  }

  reset() { this.tracks = []; }

  /**
   * @param {Array} dets  [{x1,y1,x2,y2,score,cls}]
   * @returns {Array} tracks đang sống [{id,x1..,cls,score,cxs,cys,vx,age,lost}]
   *          cxs/cys là tâm ĐÃ LÀM MƯỢT.
   */
  update(dets) {
    const high = dets.filter(d => d.score >= this.high);
    const low  = dets.filter(d => d.score < this.high && d.score >= this.low);

    for (const t of this.tracks) t.matched = false;

    // --- vòng 1: ghép track với detection điểm CAO theo IoU ---
    this._associate(this.tracks, high);
    // --- vòng 2: track còn lại ghép với detection điểm THẤP (cứu track) ---
    const unmatched = this.tracks.filter(t => !t.matched);
    this._associate(unmatched, low);

    // --- detection cao chưa ghép -> tạo track mới ---
    for (const d of high) {
      if (d._used) continue;
      this.tracks.push(this._newTrack(d));
    }

    // --- cập nhật vòng đời track ---
    const alive = [];
    for (const t of this.tracks) {
      if (t.matched) { t.lost = 0; t.age++; }
      else {
        t.lost++; t.age++;
        // dự đoán trôi theo vận tốc khi mất
        t.cxs += t.vx; t.cys += t.vy;
      }
      if (t.lost <= this.maxLost) alive.push(t);
    }
    this.tracks = alive;
    return this.tracks.filter(t => t.lost === 0);
  }

  _associate(tracks, dets) {
    // ghép tham lam theo IoU lớn nhất
    const pairs = [];
    for (let ti = 0; ti < tracks.length; ti++) {
      if (tracks[ti].matched) continue;
      for (let di = 0; di < dets.length; di++) {
        if (dets[di]._used) continue;
        const ov = iou(tracks[ti], dets[di]);
        if (ov >= this.iouThr) pairs.push([ov, ti, di]);
      }
    }
    pairs.sort((a, b) => b[0] - a[0]);
    for (const [, ti, di] of pairs) {
      const t = tracks[ti], d = dets[di];
      if (t.matched || d._used) continue;
      this._apply(t, d); d._used = true;
    }
  }

  _newTrack(d) {
    return {
      id: ++this._id, cls: d.cls, score: d.score,
      x1:d.x1, y1:d.y1, x2:d.x2, y2:d.y2,
      cxs: cx(d), cys: cy(d), vx: 0, vy: 0,
      age: 1, lost: 0, matched: true,
    };
  }

  _apply(t, d) {
    const ncx = cx(d), ncy = cy(d);
    const s = this.smooth;
    const sx = t.cxs + (ncx - t.cxs) * s;
    const sy = t.cys + (ncy - t.cys) * s;
    t.vx = sx - t.cxs; t.vy = sy - t.cys;
    t.cxs = sx; t.cys = sy;
    t.x1=d.x1; t.y1=d.y1; t.x2=d.x2; t.y2=d.y2;
    t.cls = d.cls; t.score = d.score; t.matched = true;
  }
}
