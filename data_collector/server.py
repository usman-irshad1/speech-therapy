"""
Urdu Child Speech Data Collector — Local Recording Server
Runs a local web server at http://localhost:8000 and automatically saves audio 
recordings sent from the web app directly into data_collector/recordings/{child_id}/
"""

import os
import sys
import json
import re
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
RECORDINGS_DIR = BASE_DIR / "recordings"

class DataCollectorHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    def do_POST(self):
        if self.path == "/api/save_audio":
            self.handle_save_audio()
        else:
            self.send_error(404, "Endpoint Not Found")

    def handle_save_audio(self):
        try:
            content_type = self.headers.get("Content-Type", "")
            if not content_type.startswith("multipart/form-data"):
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b'{"error": "Expected multipart/form-data"}')
                return

            boundary = content_type.split("boundary=")[-1].encode("utf-8")
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)

            # Simple multipart parser for audio blob and fields
            parts = body.split(b"--" + boundary)
            fields = {}
            file_data = None
            filename = "recording.webm"

            for part in parts:
                if not part or part == b"--\r\n":
                    continue
                header_data, _, body_data = part.partition(b"\r\n\r\n")
                body_data = body_data.rstrip(b"\r\n")
                header_str = header_data.decode("utf-8", errors="ignore")

                if 'name="audio"' in header_str:
                    match = re.search(r'filename="([^"]+)"', header_str)
                    if match:
                        filename = match.group(1)
                    file_data = body_data
                else:
                    match = re.search(r'name="([^"]+)"', header_str)
                    if match:
                        field_name = match.group(1)
                        fields[field_name] = body_data.decode("utf-8", errors="ignore")

            child_id = fields.get("child_id", "Child_001").strip()
            take_no = fields.get("take_no", "1").strip()
            word_id = fields.get("word_id", "1").strip()
            transliteration = fields.get("transliteration", "word").strip()

            # Sanitize folder names
            child_dir = re.sub(r'[^\w\-]', '_', child_id)
            save_folder = RECORDINGS_DIR / child_dir / f"Take_{take_no}"
            save_folder.mkdir(parents=True, exist_ok=True)

            out_filename = f"{int(word_id):02d}_{transliteration}.webm"
            out_path = save_folder / out_filename

            if file_data:
                with open(out_path, "wb") as f:
                    f.write(file_data)
                print(f"[+] Saved recording to: {out_path}")

            response_data = json.dumps({
                "status": "success",
                "saved_path": str(out_path.relative_to(BASE_DIR))
            }).encode("utf-8")

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(response_data)))
            self.end_headers()
            self.wfile.write(response_data)

        except Exception as e:
            print(f"[!] Error saving audio: {e}")
            self.send_response(500)
            self.end_headers()
            self.wfile.write(f'{{"error": "{str(e)}"}}'.encode("utf-8"))

def run_server(port=8000):
    RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)
    server_address = ("", port)
    httpd = HTTPServer(server_address, DataCollectorHandler)
    print("=" * 65)
    print(f"🎙️  Urdu Child Speech Data Collector Server is running!")
    print(f"👉 Open in your browser: http://localhost:{port}")
    print(f"📂 Audio recordings will save to: {RECORDINGS_DIR}")
    print("=" * 65)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")

if __name__ == "__main__":
    port = 8000
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    run_server(port)
