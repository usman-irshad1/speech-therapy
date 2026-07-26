"""
Diagnostic: print the RAW eSpeak --ipa output for a few multi-word
sentences, before any of our postprocessing/tokenization touches it.

We need to see this directly rather than guess -- the word/segment
mismatch warnings suggest eSpeak's real multi-word spacing behavior
doesn't match what the (mocked) tests assumed.

Usage:
    python debug_raw_espeak.py
"""
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

if __name__ == "__main__":
    g2p = UrduG2P()

    test_sentences = [
        "آج دھوپ ہے",                    # 3 words, zero punctuation -- mismatched 3 vs 2
        "یہ سوچ غلط ہے۔",                 # 4 words (period attached, no space) -- mismatched 4 vs 3
        "وہ عورت ہے",                     # 3 words, zero punctuation -- mismatched 3 vs 2
        "کیا بات ہے",                     # 3 words, zero punctuation -- mismatched 3 vs 2
        "کھڑا بڑا",                       # single-word-like control: 2 simple known words
    ]

    for sentence in test_sentences:
        normalized = g2p._normalize(sentence)
        raw = g2p._espeak_call(normalized)
        processed = g2p._postprocess(raw)

        print(f"input:      {sentence!r}")
        print(f"normalized: {normalized!r}  ({len(normalized.split(' '))} words)")
        print(f"raw eSpeak: {raw!r}")
        print(f"postprocessed: {processed!r}")
        print(f"space count in raw: {raw.count(' ')}")
        print("-" * 70)