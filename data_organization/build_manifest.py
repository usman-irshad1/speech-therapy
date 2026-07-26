"""
Step 2: build the actual training manifest (audio_path -> phoneme_labels)
from Common Voice Urdu, filtering out rows that shouldn't reach training.

Produces manifest CSVs for train/dev/test with columns:
    audio_path, sentence, phonemes, n_unk

Rows are DROPPED (not silently kept) if:
  - the sentence is flagged as mixed-script contaminated
  - the phoneme output contains ANY [UNK] token
    (better to lose a few rows now than train on a partially-wrong label)

Usage:
    python build_manifest.py
"""
import csv
import os
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from g2p.urdug2p import UrduG2P
except ImportError:
    from urdug2p import UrduG2P

CV_ROOT = (r"C:\Users\usman\Desktop\spech_pipeline\cache\datasets\cookiefinder"
           r"\mozilla-common-voice-urdu\versions\1")
CLIPS_DIR = os.path.join(CV_ROOT, "clips")
OUT_DIR = r"C:\Users\usman\Desktop\spech_pipeline\manifests"

SPLITS = ["train", "dev", "test"]


def build_split(g2p: UrduG2P, split: str):
    in_path = os.path.join(CV_ROOT, f"{split}.tsv")
    out_path = os.path.join(OUT_DIR, f"{split}_manifest.csv")

    n_total = 0
    n_kept = 0
    n_dropped_mixed_script = 0
    n_dropped_unk = 0

    with open(in_path, encoding="utf-8") as f_in, \
         open(out_path, "w", encoding="utf-8", newline="") as f_out:

        reader = csv.DictReader(f_in, delimiter="\t")
        writer = csv.writer(f_out)
        writer.writerow(["audio_path", "sentence", "phonemes", "n_unk"])

        for row in reader:
            n_total += 1
            sentence = row["sentence"]
            clip_filename = row["path"]
            audio_path = os.path.join(CLIPS_DIR, clip_filename)

            if not os.path.exists(audio_path):
                # mp3 filename in the TSV doesn't match what's on disk —
                # worth knowing about rather than silently skipping forever
                print(f"[WARN] audio file missing, skipping: {audio_path}")
                continue

            if g2p.flag_mixed_script(sentence):
                n_dropped_mixed_script += 1
                continue

            phonemes = g2p.text_to_phonemes(sentence)
            n_unk = phonemes.split().count("[UNK]")

            if n_unk > 0:
                n_dropped_unk += 1
                continue

            writer.writerow([audio_path, sentence, phonemes, n_unk])
            n_kept += 1

    print(f"\n[{split}] total={n_total}  kept={n_kept}  "
          f"dropped_mixed_script={n_dropped_mixed_script}  dropped_unk={n_dropped_unk}")
    print(f"[{split}] manifest written to {out_path}")


if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    g2p = UrduG2P()
    g2p.save_vocab(os.path.join(OUT_DIR, "urdu_phoneme_vocab.json"))

    for split in SPLITS:
        build_split(g2p, split)