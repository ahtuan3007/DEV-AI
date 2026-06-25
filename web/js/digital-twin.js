// ============================================================
//  DIGITAL TWIN  ·  Điều khiển phòng bệnh giả lập (SVG)
// ============================================================
export class DigitalTwin {
  constructor() {
    this.room = document.getElementById('room');
    this.stage = document.getElementById('twin-stage');
    this.sosFrame = document.getElementById('sos-frame');
    this.twinState = document.getElementById('twin-state');
    this.state = { light:false, bedUp:false, curtainOpen:false, sos:false, calling:false };
    this._sosTimer = null; this._callTimer = null;
    this._chips = {
      light:[document.getElementById('chip-light'), document.getElementById('v-light')],
      bed:[document.getElementById('chip-bed'), document.getElementById('v-bed')],
      curtain:[document.getElementById('chip-curtain'), document.getElementById('v-curtain')],
    };
  }

  _flashChip(key){ const c=this._chips[key][0]; if(!c)return; c.classList.remove('flash'); void c.offsetWidth; c.classList.add('flash'); }
  _setState(t){ this.twinState.textContent = t; }

  // ✊ Nắm tay → bật/tắt đèn (đổi nền tối ↔ sáng ấm)
  toggleLight() {
    this.state.light = !this.state.light;
    this.room.classList.toggle('lights-on', this.state.light);
    this._chips.light[1].textContent = this.state.light ? 'Bật' : 'Tắt';
    this._flashChip('light');
    this._setState(this.state.light ? 'Đèn đang BẬT' : 'Đèn đang TẮT');
    return this.state.light;
  }

  // ☝️ Chỉ ngón trỏ → nâng/hạ đầu giường
  toggleBed() {
    this.state.bedUp = !this.state.bedUp;
    this.room.classList.toggle('bed-up', this.state.bedUp);
    this._chips.bed[1].textContent = this.state.bedUp ? 'Nâng' : 'Phẳng';
    this._flashChip('bed');
    this._setState(this.state.bedUp ? 'Giường đang NÂNG' : 'Giường đã HẠ');
    return this.state.bedUp;
  }

  // 👈👉 Vuốt → kéo/mở rèm
  setCurtain(open) {
    this.state.curtainOpen = open;
    this.room.classList.toggle('curtain-open', open);
    this._chips.curtain[1].textContent = open ? 'Mở' : 'Đóng';
    this._flashChip('curtain');
    this._setState(open ? 'Rèm đã MỞ' : 'Rèm đã ĐÓNG');
    return open;
  }

  // 🖐️ Xòe tay → SOS: viền nhấp nháy + còi quay
  triggerSOS() {
    this.state.sos = true;
    this.sosFrame.classList.add('active');
    this.room.classList.add('sos');
    this.stage.classList.add('sos');
    this._setState('⚠️ BÁO ĐỘNG SOS');
    setTimeout(()=>this.stage.classList.remove('sos'), 1100);
    clearTimeout(this._sosTimer);
    this._sosTimer = setTimeout(()=>this.clearSOS(), 6000); // tự tắt sau 6s
  }
  clearSOS() {
    this.state.sos = false;
    this.sosFrame.classList.remove('active');
    this.room.classList.remove('sos');
    this._setState('Đã xử lý báo động');
  }

  // 👋 Vẫy tay → hộp thoại "Đang gọi bác sĩ..."
  callDoctor() {
    this.state.calling = true;
    this.room.classList.add('calling');
    this._setState('📞 Đang gọi bác sĩ…');
    clearTimeout(this._callTimer);
    this._callTimer = setTimeout(()=>{
      this.state.calling = false;
      this.room.classList.remove('calling');
      this._setState('Bác sĩ đã nhận cuộc gọi');
    }, 5000);
  }
}
