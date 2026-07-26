import os
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from testing.gop import run_gop_pipeline
except ImportError:
    from gop import run_gop_pipeline

# Directory where your generated MP3 files are stored
AUDIO_DIR = r"C:\Users\usman\Desktop\spech_pipeline\comprehensive_word_audio"

# Dictionary mapping filename to its exact Urdu text word
test_corpus = {
    "پانی.mp3": "پانی",
    "گھر.mp3": "گھر",
    "کتاب.mp3": "کتاب",
    "آڑو.mp3": "آڑو",
    "باڑھ.mp3": "باڑھ",
    "ٹاٹ.mp3": "ٹاٹ",
    "ڈالی.mp3": "ڈالی",
    "ڈھکن.mp3": "ڈھکن",
    "ٹھیکہ.mp3": "ٹھیکہ",
    "پاک.mp3": "پاک",
    "پھول.mp3": "پھول",
    "باب.mp3": "باب",
    "بھول.mp3": "بھول",
    "کام.mp3": "کام",
    "کھال.mp3": "کھال",
    "چپ.mp3": "چپ",
    "چھال.mp3": "چھال",
    "جام.mp3": "جام",
    "جھاڑو.mp3": "جھاڑو",
    "شام.mp3": "شام",
    "فال.mp3": "فال",
    "خام.mp3": "خام",
    "غالب.mp3": "غالب",
    "نام.mp3": "نام",
    "منہ.mp3": "منہ",
    "یوں.mp3": "یوں",
    "جاں.mp3": "جاں",
    "پیلا.mp3": "پیلا",
    "بین.mp3": "بین",
    "گانا.mp3": "گانا",
    "رات.mp3": "رات",
    "لکھن.mp3": "لکھن",
    "وقت.mp3": "وقت",
    "ساده.mp3": "ساده",
    "بیمار.mp3": "بیمار"
}

if __name__ == "__main__":
    print("=== Starting Batch GOP Evaluation for STAPPU Words ===")
    
    summary_results = {}
    
    for filename, urdu_word in test_corpus.items():
        audio_path = os.path.join(AUDIO_DIR, filename)
        
        if not os.path.exists(audio_path):
            print(f"\n[Skipped] File not found: {audio_path}")
            continue
            
        print(f"\n--------------------------------------------------")
        print(f"Evaluating Word: '{urdu_word}' ({filename})")
        print(f"--------------------------------------------------")
        
        try:
            results = run_gop_pipeline(audio_path, urdu_word, is_raw_phonemes=False)
            summary_results[urdu_word] = results
        except Exception as e:
            print(f"[Error] Failed processing '{urdu_word}': {e}")

    print("\n=== Batch Testing Complete ===")