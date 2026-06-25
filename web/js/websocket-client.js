// ============================================================
//  WEBSOCKET CLIENT  ·  Cầu nối tới backend Python AI (camera thật)
//  ------------------------------------------------------------
//  Backend chỉ cần gửi JSON mỗi khi nhận diện được cử chỉ:
//     { "gesture": "Nam_Tay", "confidence": 0.94 }
//  hoặc dùng id của web: { "gesture": "fist" }
//  Map model→id được xử lý ở app.js (GESTURES[].model).
// ============================================================
import { WS_URL } from './config.js';

export class WSClient {
  /**
   * @param {object} o
   * @param {(msg:object)=>void} o.onGesture  nhận {gesture, confidence}
   * @param {(state:string)=>void} o.onStatus  'connecting'|'open'|'closed'|'error'
   */
  constructor({ onGesture, onStatus, url = WS_URL }) {
    this.url = url; this.onGesture = onGesture; this.onStatus = onStatus;
    this.ws = null; this.manualClose = false;
  }

  connect(url) {
    if (url) this.url = url;
    this.manualClose = false;
    this.onStatus?.('connecting');
    try { this.ws = new WebSocket(this.url); }
    catch (e) { this.onStatus?.('error'); return; }

    this.ws.onopen  = () => this.onStatus?.('open');
    this.ws.onclose = () => this.onStatus?.(this.manualClose ? 'closed' : 'error');
    this.ws.onerror = () => this.onStatus?.('error');
    this.ws.onmessage = (ev) => {
      let data; try { data = JSON.parse(ev.data); } catch { data = { gesture: String(ev.data) }; }
      if (data && data.gesture) this.onGesture?.(data);
    };
  }

  disconnect() {
    this.manualClose = true;
    if (this.ws) { this.ws.close(); this.ws = null; }
    this.onStatus?.('closed');
  }

  get connected(){ return this.ws && this.ws.readyState === WebSocket.OPEN; }
}
