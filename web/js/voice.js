// ============================================================
//  VOICE ANNOUNCER  ·  Phát âm thanh tiếng Việt khi có cử chỉ
//  Dùng Web Speech API (SpeechSynthesis) — 100% offline.
//  Chrome/Edge hỗ trợ giọng vi-VN tốt nhất.
// ============================================================

export class VoiceAnnouncer {
  constructor() {
    this.enabled = true;
    this._synth = window.speechSynthesis;
    this._voice = null;
    this._lastSpeak = 0;
    this._cooldownMs = 1500;
    this._supported = !!this._synth;

    if (this._supported) {
      this._pickVoice();
      if (this._synth.onvoiceschanged !== undefined) {
        this._synth.onvoiceschanged = () => this._pickVoice();
      }
    }
  }

  _pickVoice() {
    const voices = this._synth.getVoices();
    this._voice =
      voices.find(v => v.lang === 'vi-VN') ||
      voices.find(v => v.lang.startsWith('vi')) ||
      voices[0] || null;
  }

  speak(text) {
    if (!this._supported || !this.enabled) return false;
    const now = Date.now();
    if (now - this._lastSpeak < this._cooldownMs) return false;
    this._lastSpeak = now;
    this._synth.cancel();
    const utt = new SpeechSynthesisUtterance(text);
    utt.lang = 'vi-VN';
    utt.rate = 1.05;
    utt.pitch = 1.0;
    utt.volume = 1.0;
    if (this._voice) utt.voice = this._voice;
    this._synth.speak(utt);
    return true;
  }

  toggle() {
    this.enabled = !this.enabled;
    if (!this.enabled) this._synth?.cancel();
    return this.enabled;
  }

  get isSupported() { return this._supported; }
}
