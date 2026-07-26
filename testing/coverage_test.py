"""
Step 1: run the phoneme-coverage audit on the REAL corpus (not word lists).

Usage:
    python run_coverage_audit.py
"""
import os
import sys
import json
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from g2p.urdug2p import UrduG2P
    from g2p.urdu_g2p_patches import audit_phoneme_coverage
except ImportError:
    from urdug2p import UrduG2P
    from urdu_g2p_patches import audit_phoneme_coverage

CV_ROOT = (r"C:\Users\usman\Desktop\spech_pipeline\cache\datasets\cookiefinder"
           r"\mozilla-common-voice-urdu\versions\1")

if __name__ == "__main__":
    g2p = UrduG2P()

    vocab_file = PROJECT_ROOT / "urdu_phoneme_vocab.json"
    if not vocab_file.exists():
        vocab_file = PROJECT_ROOT / "manifests" / "urdu_phoneme_vocab.json"

    with open(vocab_file, encoding="utf-8") as f:
        vocab = json.load(f)

    # Start with a limit for a fast first pass (a few thousand rows), then
    # rerun with limit=None once you trust the pipeline isn't going to choke
    # partway through a 20k+ row file.
    counter, zero_coverage, bad_rows = audit_phoneme_coverage(
        f"{CV_ROOT}\\validated.tsv",
        g2p, vocab,
        sentence_col="sentence",
        limit=500,
    )

    # Compile errors and coverage gaps into a dictionary for export
    error_report = {
        "zero_coverage_phonemes": zero_coverage,
        "bad_rows_count": len(bad_rows),
        "bad_rows": bad_rows
    }

    # Write errors to a file
    report_filename = "audit_errors_report.json"
    with open(report_filename, "w", encoding="utf-8") as error_file:
        json.dump(error_report, error_file, ensure_ascii=False, indent=4)

    print(f"\n[Info] Errors and flags successfully written to {report_filename}")

    print("\n--- Per-phoneme counts (sorted, rarest first) ---")
    for phoneme, count in sorted(counter.items(), key=lambda x: x[1]):
        print(f"{phoneme:6} {count}")

    print(f"\n{len(bad_rows)} rows flagged as mixed-script and skipped.")
    if zero_coverage:
        print(f"\nZERO-coverage phonemes (need attention): {zero_coverage}")