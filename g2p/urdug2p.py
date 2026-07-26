import os
import re
import json
import subprocess
import tempfile


class UrduG2P:
    def __init__(self):
        self.vocab_dict = {"[PAD]": 0, "[UNK]": 1, "|": 2}
        phonemes = [
            "p", "pʰ", "b", "bʰ", "t", "tʰ", "d", "dʰ", "ʈ", "ʈʰ", "ɖ", "ɖʰ", "k", "kʰ", "g", "gʰ", "q",
            "tʃ", "tʃʰ", "dʒ", "dʒʰ", "f", "s", "z", "ʃ", "x", "ɣ", "h", "ʒ",
            "m", "n", "ŋ", "l", "r", "ɽ", "ɽʰ", "j", "w",
            "i", "e", "ɛ", "ɑ", "ə", "ɪ", "ʊ", "u", "o", "ɔ",
            # Nasalized vowels
            "ĩ", "ẽ", "ɑ̃", "ɪ̃", "ʊ̃", "ũ", "õ", "ɔ̃",
        ]
        for idx, p in enumerate(phonemes, start=3):
            self.vocab_dict[p] = idx

        self.espeak_path = r"C:\Program Files\eSpeak NG\espeak-ng.exe"

        self.mappings = {
            # Standard IPA Mappings
            'ɟ': 'dʒ', 'ɡ': 'g', 'ʋ': 'w', 'ʂ': 'ʃ', 'ʐ': 'z',
            'cʰ': 'tʃʰ', 'c': 'tʃ',
            'pʰ': 'pʰ', 'bʰ': 'bʰ', 'tʰ': 'tʰ', 'dʰ': 'dʰ',
            'ʈʰ': 'ʈʰ', 'ɖʰ': 'ɖʰ', 'kʰ': 'kʰ', 'gʰ': 'gʰ',
            'aː': 'ɑ', 'a': 'ɑ', 'oː': 'o', 'o': 'o',
            'uː': 'u', 'u': 'u', 'iː': 'i', 'i': 'i',
            'eː': 'e', 'e': 'e',
            # Cleaning Markers
            'ˈ': '', 'ˌ': '', 'ː': '', 'ʌ': 'ə', 'ʔ': '',
            't.': 'ʈ', 'd.': 'ɖ', 'n.': 'n', 'r.': 'r',
            'A': 'ɑ', 'E': 'ɛ', 'I': 'ɪ', 'O': 'ɔ', 'U': 'ʊ',
            'X': 'x', 'G': 'ɣ', 'N': 'ŋ', 'R': 'ɽ',
            '\u0303': '',  # Strip combining tilde (raw eSpeak rarely emits this correctly anyway)
        }
        self.sorted_mappings = sorted(self.mappings.items(), key=lambda x: len(x[0]), reverse=True)

        # Aspiration-collapse rules -- applied PER WORD in _postprocess
        # (never across word boundaries; see that method's docstring for why).
        self._aspiration_collapse_rules = [
            ('p h', 'pʰ'), ('b h', 'bʰ'), ('t h', 'tʰ'), ('d h', 'dʰ'),
            ('ʈ h', 'ʈʰ'), ('ɖ h', 'ɖʰ'), ('k h', 'kʰ'), ('g h', 'gʰ'),
            ('tʃ h', 'tʃʰ'), ('dʒ h', 'dʒʰ'),
        ]

        # --- Grapheme-level override constants (Section 15/16 fixes) ---
        self.RETROFLEX_FLAP_CHAR = 'ڑ'   # U+0691
        self.PLAIN_R_CHAR = 'ر'          # U+0631
        self.NOON_GHUNNA_CHAR = 'ں'      # U+06BA (distinct from regular ن)
        self.NASAL_VOWEL_MAP = {
            'i': 'ĩ', 'e': 'ẽ', 'ɑ': 'ɑ̃', 'ɪ': 'ɪ̃',
            'ʊ': 'ʊ̃', 'u': 'ũ', 'o': 'õ', 'ɔ': 'ɔ̃',
        }
        self._latin_re = re.compile(r'[a-zA-Z]')

    # -------------------------------------------------------------
    # Main entry point
    # -------------------------------------------------------------
    def text_to_phonemes(self, text: str) -> str:
        normalized = self._normalize(text)
        raw = self._espeak_call(normalized)
        processed = self._postprocess(raw)
        tokens = self._tokenize_to_vocab(processed)          # list, '|' at word boundaries
        tokens = self._apply_overrides_per_word(normalized, tokens)
        return ' '.join(tokens)

    def _apply_overrides_per_word(self, normalized_text: str, tokens: list) -> list:
        """
        The retroflex (ɽ) and nasalization (ں) overrides must be scoped to
        the SPECIFIC WORD that contains the triggering grapheme, not applied
        over the whole sentence — otherwise, e.g., ں in an early word of a
        multi-word sentence can end up incorrectly nasalizing a vowel in a
        later, unrelated word. Split both the source text and the token
        list (on '|', which _tokenize_to_vocab now emits at word boundaries)
        into per-word chunks, apply the overrides within each word, then
        rejoin. Falls back to whole-sentence processing (with a warning) if
        the word count and '|'-delimited segment count don't match — this
        can happen if eSpeak drops/merges a word outright, and guessing an
        alignment in that case would risk mislabeling worse than skipping.
        """
        words = normalized_text.split(' ')

        segments = []
        current = []
        for t in tokens:
            if t == '|':
                segments.append(current)
                current = []
            else:
                current.append(t)
        segments.append(current)

        if len(words) != len(segments):
            print(f"[WARN] word/segment count mismatch ({len(words)} words vs "
                  f"{len(segments)} segments) for '{normalized_text}' — "
                  f"applying overrides sentence-wide instead of per-word")
            tokens = self._apply_retroflex_override(normalized_text, tokens)
            tokens = self._merge_retroflex_aspiration(tokens)
            tokens = self._apply_nasalization_override(normalized_text, tokens)
            return tokens

        new_segments = []
        for word, seg in zip(words, segments):
            seg = self._apply_retroflex_override(word, seg)
            seg = self._merge_retroflex_aspiration(seg)
            seg = self._apply_nasalization_override(word, seg)
            new_segments.append(seg)

        result = []
        for idx, seg in enumerate(new_segments):
            result.extend(seg)
            if idx != len(new_segments) - 1:
                result.append('|')
        return result

    def _espeak_call(self, text: str) -> str:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.txt', delete=False) as f:
            f.write(text)
            temp_path = f.name
        try:
            result = subprocess.run(
                [self.espeak_path, "-v", "ur", "-f", temp_path, "--ipa", "-q"],
                capture_output=True, text=True, encoding="utf-8"
            )
            return result.stdout.strip()
        finally:
            os.unlink(temp_path)

    def _normalize(self, text: str) -> str:
        text = re.sub(r'[^\u0600-\u06FF\s]', '', text)
        return re.sub(r'\s+', ' ', text).strip()

    def _postprocess(self, phonemes: str) -> str:
        """
        Applies both the sorted_mappings replacements and the aspiration-
        collapse rules PER WORD (splitting on whitespace first), not on the
        whole string at once. This is required: applying replacements like
        ('p h', 'pʰ') directly on the full string was confirmed to fire
        ACROSS word boundaries whenever one word ends in an unaspirated
        stop and the next word starts with 'h' -- extremely common in Urdu
        because ہے ("is/are") is one of the most frequent words in the
        language. That bug was silently deleting the space between words
        AND fabricating an aspirated consonant that was never in the
        source audio, corrupting both word-boundary tracking and the
        phoneme content itself. Verified against real eSpeak output for
        'دھوپ ہے' (raw 'dʰˈoːp hɛ' was becoming 'dʰopʰɛ') before this fix.
        """
        words = phonemes.split(' ')
        processed_words = []
        for word in words:
            w = word
            for old, new in self.sorted_mappings:
                w = w.replace(old, new)
            for old, new in self._aspiration_collapse_rules:
                w = w.replace(old, new)
            processed_words.append(w)
        return ' '.join(processed_words)

    def _tokenize_to_vocab(self, phonemes: str) -> list:
        """
        Returns a LIST of tokens (not a joined string) so the grapheme-level
        overrides below can index into it positionally before the final join.

        Whitespace in the eSpeak output marks word boundaries for multi-word
        input (e.g. full Common Voice sentences) — these are converted to a
        single '|' word-delimiter token per run of whitespace, rather than
        silently discarded, so multi-word phoneme sequences don't collapse
        into one undifferentiated stream with no boundary information.
        """
        multi_char = sorted(
            [p for p in self.vocab_dict.keys() if len(p) > 1 and not p.startswith("[")],
            key=len, reverse=True
        )
        tokens = []
        i = 0
        prev_was_space = False
        while i < len(phonemes):
            if phonemes[i] in [' ', '\n', '\r']:
                if not prev_was_space and tokens:
                    tokens.append('|')
                prev_was_space = True
                i += 1
                continue
            prev_was_space = False

            matched = False
            for mc in multi_char:
                if phonemes[i:i + len(mc)] == mc:
                    tokens.append(mc)
                    i += len(mc)
                    matched = True
                    break
            if matched:
                continue

            c = phonemes[i]
            tokens.append(c if c in self.vocab_dict else "[UNK]")
            i += 1

        if tokens and tokens[-1] == '|':
            tokens.pop()
        return tokens

    # -------------------------------------------------------------
    # Grapheme-level overrides (fixes confirmed dead phonemes: ɽ, nasal vowels)
    # -------------------------------------------------------------
    def _r_grapheme_flags(self, original_text: str):
        """Left-to-right booleans over every ر/ڑ in the source text: True=ڑ, False=ر."""
        flags = []
        for ch in original_text:
            if ch == self.RETROFLEX_FLAP_CHAR:
                flags.append(True)
            elif ch == self.PLAIN_R_CHAR:
                flags.append(False)
        return flags

    def _apply_retroflex_override(self, original_text: str, tokens: list) -> list:
        """
        Forces plain 'r' tokens to 'ɽ' wherever the source grapheme was ڑ,
        using positional alignment between ر/ڑ graphemes and 'r' output tokens.
        Skips (with a warning) if counts don't match rather than guessing wrong.
        """
        flags = self._r_grapheme_flags(original_text)
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

    def _merge_retroflex_aspiration(self, tokens: list) -> list:
        """
        Merges an 'ɽ' token immediately followed by a standalone 'h' token
        into a single 'ɽʰ' (aspirated retroflex flap) — e.g. داڑھی (beard).

        MUST run after _apply_retroflex_override: eSpeak itself never emits
        'ɽ' (it has no concept of the retroflex flap at all), so at
        _postprocess time the sequence is still plain 'r h', not 'ɽ h'.
        The other aspirated consonants (pʰ, bʰ, tʰ, ...) get collapsed
        earlier in _postprocess because eSpeak *does* emit their plain
        forms directly; ɽ is the one exception that only exists after our
        own override runs, so its aspiration merge has to happen here,
        one stage later than the others.
        """
        merged = []
        i = 0
        while i < len(tokens):
            if tokens[i] == 'ɽ' and i + 1 < len(tokens) and tokens[i + 1] == 'h':
                merged.append('ɽʰ')
                i += 2
            else:
                merged.append(tokens[i])
                i += 1
        return merged

    def _apply_nasalization_override(self, original_text: str, tokens: list) -> list:
        """
        If the source word contains ں (noon ghunna, NOT regular ن), nasalizes
        the last oral vowel token found. Covers the dominant word-final
        pattern (گاؤں, ہندوؤں, میں, کہاں); mid-word ں isn't specially handled.

        Also strips a redundant trailing 'n' token if eSpeak emitted BOTH a
        nasalized-sounding vowel context AND a literal consonantal 'n' right
        after it (observed for گاؤں/ہندوؤں but not میں/کہاں) — without this,
        the word ends up double-marked as nasal (vowel + trailing n).
        """
        if self.NOON_GHUNNA_CHAR not in original_text:
            return tokens

        for i in range(len(tokens) - 1, -1, -1):
            if tokens[i] in self.NASAL_VOWEL_MAP:
                tokens[i] = self.NASAL_VOWEL_MAP[tokens[i]]
                # Drop a redundant word-final 'n' immediately after the vowel
                # we just nasalized — it's eSpeak double-encoding the same ں.
                if i + 1 < len(tokens) and tokens[i + 1] == 'n' and i + 1 == len(tokens) - 1:
                    tokens.pop(i + 1)
                break
        else:
            print(f"[WARN] '{original_text}' contains ں but no oral vowel "
                  f"token found to nasalize — check output manually")
        return tokens

    # -------------------------------------------------------------
    # Mixed-script / Latin contamination check
    # -------------------------------------------------------------
    def flag_mixed_script(self, text: str) -> bool:
        """True if `text` (nominally Urdu) contains Latin a-z/A-Z letters."""
        return bool(self._latin_re.search(text))

    def save_vocab(self, path="urdu_phoneme_vocab.json"):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.vocab_dict, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    g2p = UrduG2P()
    g2p.save_vocab()

    # Targeted regression test for the two fixes — every word here contains
    # either ڑ (retroflex flap) or ں (nasalization), plus a couple of the
    # mixed-script / Arabic-liturgical edge cases from the coverage audit.
    regression_words = [
        # ڑ retroflex flap — should now show 'ɽ', not 'r'
        "کھڑا", "بڑا", "دوڑنا", "چڑیا", "پہاڑ", "جھاڑی", "گھڑی", "پکڑنا",
        # ں nasalization — should now show a nasalized vowel
        "گاؤں", "ہندوؤں", "میں", "کہاں",
        # words with BOTH ر and ڑ, to test the alignment safety fallback
        "چوہدری", "دروازہ",
        # known-bad mixed-script entries — should be flagged, not silently mangled
        "ادrak", "رahim", "ulta",
        # original 8-word smoke test for a general sanity check
        "پاکستان", "اردو", "بچہ", "کتاب", "پانی", "چھوٹی", "بھارت", "کھانا",
    ]

    print("\n=== Regression Test: ɽ / nasalization fixes + mixed-script flags ===")
    for word in regression_words:
        if g2p.flag_mixed_script(word):
            print(f"{word:10} → [SKIPPED: mixed-script contamination flagged]")
            continue
        print(f"{word:10} → {g2p.text_to_phonemes(word)}")