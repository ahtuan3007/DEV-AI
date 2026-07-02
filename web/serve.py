# ============================================================
#  Server cục bộ cho Web Dashboard (offline)
#  Ép đúng MIME type cho .js / .mjs / .wasm  (sửa lỗi mà
#  http.server mặc định trên Windows hay trả text/plain).
# ============================================================
import http.server, socketserver, os, sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
os.chdir(os.path.dirname(os.path.abspath(__file__)))

class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        ".js":   "text/javascript",
        ".mjs":  "text/javascript",
        ".wasm": "application/wasm",
        ".json": "application/json",
        ".onnx": "application/octet-stream",
        ".css":  "text/css",
        ".html": "text/html",
    }
    def end_headers(self):
        # tránh cache để luôn nạp code mới khi đang phát triển
        self.send_header("Cache-Control", "no-store")
        # Cô lập nguồn -> bật SharedArrayBuffer -> onnxruntime-web chạy ĐA LUỒNG.
        # COEP 'credentialless' để vẫn tải được Google Fonts (cross-origin).
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "credentialless")
        super().end_headers()
    def log_message(self, *a):
        pass  # gọn console

with socketserver.ThreadingTCPServer(("", PORT), Handler) as httpd:
    print(f"  Server: http://localhost:{PORT}")
    print(f"  Thu muc: {os.getcwd()}")
    print("  (Ctrl+C de dung)\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nDa dung server.")
