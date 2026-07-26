"""
Urdu Child Speech Data Collector — Local Recording & Real-Time GOP Server

Runs a local web server at http://localhost:8000.
When an audio recording is uploaded:
1. Saves the audio file into data_collector/recordings/{child_id}/Take_{take_no}/{01_Paani}.webm
2. Runs the Goodness-of-Pronunciation (GOP) & Forced Alignment model in real time.
3. Identifies and saves incorrect/mispronounced phoneme labels into companion JSON file ({01_Paani}_gop.json).
4. Returns real-time phoneme feedback to the browser UI.
"""

import os
import sys
import json
import re
import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

# Add project root to sys.path for model imports
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

RECORDINGS_DIR = BASE_DIR / "recordings"

# Try loading GOP pipeline from testing.gop
GOP_AVAILABLE = False
try:
    from testing.gop import run_gop_pipeline
    GOP_AVAILABLE = True
    print("[+] ML GOP & Forced Alignment Model loaded successfully!")
except Exception as e:
    print(f"[!] GOP Model import warning: {e}. (Will save audio without live GOP scoring if dependencies missing).")

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
            word_urdu = fields.get("word_urdu", "").strip()
            transliteration = fields.get("transliteration", "word").strip()

            child_dir = re.sub(r'[^\w\-]', '_', child_id)
            save_folder = RECORDINGS_DIR / child_dir / f"Take_{take_no}"
            save_folder.mkdir(parents=True, exist_ok=True)

            out_filename = f"{int(word_id):02d}_{transliteration}.webm"
            out_path = save_folder / out_filename

            if file_data:
                with open(out_path, "wb") as f:
                    f.write(file_data)
                print(f"[+] Saved recording: {out_path}")

            # Real-Time GOP Scoring & Labeling
            gop_results = None
            incorrect_phonemes = []
            json_path_str = None

            if GOP_AVAILABLE and word_urdu and out_path.exists():
                try:
                    print(f"[*] Running Real-Time GOP Analysis for '{word_urdu}'...")
                    raw_gop = run_gop_pipeline(str(out_path), word_urdu, is_raw_phonemes=False)
                    
                    phoneme_details = []
                    for r in raw_gop:
                        phone = r["phone"]
                        gop_margin = r["gop_margin"]
                        gop_max_logit = r["gop_max_logit"]
                        is_mispronounced = "MISPRONOUNCED" in r.get("flag", "") or (gop_margin is not None and gop_margin < 0.0)
                        
                        if is_mispronounced:
                            incorrect_phonemes.append(phone)

                        phoneme_details.append({
                            "phone": phone,
                            "gop_margin": round(gop_margin, 3) if gop_margin is not None else None,
                            "gop_max_logit": round(gop_max_logit, 3) if gop_max_logit is not None else None,
                            "status": "incorrect" if is_mispronounced else "correct",
                            "incorrect": is_mispronounced
                        })

                    gop_results = {
                        "word_id": int(word_id),
                        "word_urdu": word_urdu,
                        "transliteration": transliteration,
                        "timestamp": datetime.datetime.now().isoformat(),
                        "incorrect_phonemes": incorrect_phonemes,
                        "phoneme_details": phoneme_details,
                        "total_phonemes": len(phoneme_details),
                        "incorrect_count": len(incorrect_phonemes)
                    }

                    # Save companion JSON file with real-time phoneme labels
                    json_filename = f"{int(word_id):02d}_{transliteration}_gop.json"
                    json_path = save_folder / json_filename
                    with open(json_path, "w", encoding="utf-8") as jf:
                        json.dump({
                            "child_id": child_id,
                            "take_no": take_no,
                            "audio_file": out_filename,
                            "gop_analysis": gop_results
                        }, jf, ensure_ascii=False, indent=2)
                    
                    json_path_str = str(json_path.relative_to(BASE_DIR))
                    print(f"[+] Saved real-time GOP labels to: {json_path}")

                except Exception as ex:
                    print(f"[!] Real-time GOP calculation warning: {ex}")

            response_data = json.dumps({
                "status": "success",
                "saved_path": str(out_path.relative_to(BASE_DIR)),
                "json_path": json_path_str,
                "gop_results": gop_results
            }, ensure_ascii=False).encode("utf-8")

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
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
    print("=" * 70)
    print(f"🎙️  Urdu Child Speech Data Collector & Real-Time GOP Server!")
    print(f"👉 Open in browser: http://localhost:{port}")
    print(f"📂 Audio & Real-Time GOP JSON saved to: {RECORDINGS_DIR}")
    print("=" * 70)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")

if __name__ == "__main__":
    port = 8000
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    run_server(port)
