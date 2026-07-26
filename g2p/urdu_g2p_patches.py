"""
Patches for UrduG2P (urdug2p.py):
  1. Retroflex flap override:  ڑ -> ɽ  (eSpeak collapses this to plain 'r')
  2. Nasalization override:    ں triggers nasalizing the preceding vowel
  3. Mixed-script/Latin contamination validator
  4. Full-corpus phoneme coverage audit (Counter over a whole TSV)

Drop these methods into your UrduG2P class, or import this module and
monkeypatch / subclass as shown at the bottom.
"""

import re
import csv
from collections import Counter


# ---------------------------------------------------------------------
# 1. Retroflex flap override
# ---------------------------------------------------------------------

RETROFLEX_FLAP_CHAR = 'ڑ'   # U+0691
PLAIN_R_CHAR = 'ر'          # U+0631


def _r_grapheme_flags(original_text: str):
    """
    Left-to-right list of booleans over every ر/ڑ character in the
    ORIGINAL Urdu text: True = retroflex (ڑ), False = plain (ر).
    """
    flags = []
    for ch in original_text:
        if ch == RETROFLEX_FLAP_CHAR:
            flags.append(True)
        elif ch == PLAIN_R_CHAR:
            flags.append(False)
    return flags


def apply_retroflex_override(original_text: str, tokens: list) -> list:
    """
    tokens: list of phoneme tokens (NOT yet joined into a string).
    Overrides plain 'r' tokens to 'ɽ' wherever the source grapheme was ڑ,
    using positional (left-to-right) alignment.

    Safety: if the count of ر/ڑ graphemes in the input doesn't match the
    count of 'r' tokens in the output (eSpeak deleted/added a segment),
    we DON'T guess — we log a warning and leave the tokens untouched.
    Silently guessing wrong here is worse than skipping the fix for that word.
    """
    flags = _r_grapheme_flags(original_text)
    r_positions = [i for i, t in enumerate(tokens) if t == 'r']

    if len(flags) != len(r_positions):
        print(f"[WARN] retroflex override skipped for '{original_text}': "
              f"{len(flags)} ر/ڑ graphemes vs {len(r_positions)} 'r' tokens "
              f"in output (mismatch — alignment unsafe)")
        return tokens

    for is_retroflex, pos in zip(flags, r_positions):
        if is_retroflex:
            tokens[pos] = 'ɽ'
    return tokens


# ---------------------------------------------------------------------
# 2. Nasalization override (ں-triggered)
# ---------------------------------------------------------------------

NOON_GHUNNA_CHAR = 'ں'  # U+06BA — dedicated Urdu nasalization letter

NASAL_VOWEL_MAP = {
    'i': 'ĩ', 'e': 'ẽ', 'ɑ': 'ɑ̃', 'ɪ': 'ɪ̃',
    'ʊ': 'ʊ̃', 'u': 'ũ', 'o': 'õ', 'ɔ': 'ɔ̃',
}


def apply_nasalization_override(original_text: str, tokens: list) -> list:
    """
    If the source word contains ں (noon ghunna — NOT the regular ن),
    nasalize the last oral vowel token found before the end of the word.

    This is a heuristic: word-final ں is the dominant pattern in Urdu
    (گاؤں, ہندوؤں, میں, کہاں), but ں can in principle appear mid-word too,
    which this simple version won't handle correctly. Good enough as a v1
    fix for the by-far-most-common case; flag mid-word ں separately if you
    want to handle it properly later.
    """
    if NOON_GHUNNA_CHAR not in original_text:
        return tokens

    for i in range(len(tokens) - 1, -1, -1):
        if tokens[i] in NASAL_VOWEL_MAP:
            tokens[i] = NASAL_VOWEL_MAP[tokens[i]]
            break
    else:
        print(f"[WARN] '{original_text}' contains ں but no oral vowel "
              f"token found to nasalize — check output manually")
    return tokens


# ---------------------------------------------------------------------
# 3. Mixed-script / Latin contamination validator
# ---------------------------------------------------------------------

_LATIN_RE = re.compile(r'[a-zA-Z]')


def flag_mixed_script(text: str) -> bool:
    """True if `text` (nominally Urdu) contains any Latin a-z/A-Z letters."""
    return bool(_LATIN_RE.search(text))


def audit_word_list(words: list) -> list:
    """Return the subset of `words` that are mixed-script-contaminated."""
    return [w for w in words if flag_mixed_script(w)]


# ---------------------------------------------------------------------
# 4. Full-corpus phoneme coverage audit
# ---------------------------------------------------------------------

def audit_phoneme_coverage(tsv_path: str, g2p, vocab: dict,
                            sentence_col: str = 'sentence',
                            limit: int = None):
    """
    Run G2P over every row of a Common Voice-style TSV and tally how many
    times each vocab phoneme actually occurs. Skips mixed-script rows
    (reports them separately instead of feeding them to G2P).

    Returns:
        counter          - Counter of phoneme -> occurrence count
        zero_coverage    - list of phonemes that NEVER appeared (dead classes)
        mixed_script_bad - list of raw sentences flagged as contaminated
    """
    real_phonemes = [p for p in vocab if not p.startswith('[') and p != '|']
    counter = Counter({p: 0 for p in real_phonemes})
    mixed_script_bad = []
    n = 0

    with open(tsv_path, encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            text = row[sentence_col]
            if flag_mixed_script(text):
                mixed_script_bad.append(text)
                continue

            phonemes = g2p.text_to_phonemes(text).split()
            for p in phonemes:
                if p in counter:
                    counter[p] += 1

            n += 1
            if limit and n >= limit:
                break

    zero_coverage = [p for p, c in counter.items() if c == 0]
    print(f"Audited {n} utterances ({len(mixed_script_bad)} flagged/skipped "
          f"for mixed script).")
    if zero_coverage:
        print(f"Phonemes with ZERO occurrences: {zero_coverage}")
    else:
        print("Every vocab phoneme occurred at least once.")

    return counter, zero_coverage, mixed_script_bad


# ---------------------------------------------------------------------
# How to wire this into your existing UrduG2P class
# ---------------------------------------------------------------------
r"""
In urdug2p.py, change `_tokenize_to_vocab` to build and return a LIST
(not a joined string), then apply the overrides before joining:

    def _tokenize_to_vocab(self, phonemes: str) -> list:
        multi_char = sorted(
            [p for p in self.vocab_dict.keys() if len(p) > 1 and not p.startswith("[")],
            key=len, reverse=True
        )
        tokens = []
        i = 0
        while i < len(phonemes):
            if phonemes[i] in [' ', '\n', '\r']:
                i += 1; continue
            matched = False
            for mc in multi_char:
                if phonemes[i:i+len(mc)] == mc:
                    tokens.append(mc)
                    i += len(mc)
                    matched = True
                    break
            if matched:
                continue
            c = phonemes[i]
            tokens.append(c if c in self.vocab_dict else "[UNK]")
            i += 1
        return tokens   # <-- return the LIST, not ' '.join(tokens)

Then update text_to_phonemes to apply the overrides using the ORIGINAL
(pre-normalization) text, and join at the very end:

    from urdu_g2p_patches import apply_retroflex_override, apply_nasalization_override

    def text_to_phonemes(self, text: str) -> str:
        normalized = self._normalize(text)
        raw = self._espeak_call(normalized)
        processed = self._postprocess(raw)
        tokens = self._tokenize_to_vocab(processed)          # now a list
        tokens = apply_retroflex_override(normalized, tokens)
        tokens = apply_nasalization_override(normalized, tokens)
        return ' '.join(tokens)

Then re-run your smoke test — بڑا, کھڑا, دوڑنا, چڑیا should now show ɽ,
and گاؤں / ہندوؤں should show a nasalized vowel.

For the full-corpus audit, once Common Voice Urdu is loaded:

    from urdu_g2p_patches import audit_phoneme_coverage
    import json

    with open("urdu_phoneme_vocab.json", encoding="utf-8") as f:
        vocab = json.load(f)

    g2p = UrduG2P()
    counter, zero_coverage, bad_rows = audit_phoneme_coverage(
        r"C:\Users\usman\Desktop\spech_pipeline\cache\datasets\cookiefinder"
        r"\mozilla-common-voice-urdu\versions\1\validated.tsv",
        g2p, vocab, limit=None   # set a limit like 5000 for a quick first pass
    )
"""