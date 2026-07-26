import os
import re
import json
import subprocess

ESPEAK_PATH = r"C:\Program Files\eSpeak NG\espeak-ng.exe"

def build_vocab():
    phonemes = {
        "p": 0, "pʰ": 1, "b": 2, "bʰ": 3,
        "t": 4, "tʰ": 5, "d": 6, "dʰ": 7,
        "ʈ": 8, "ʈʰ": 9, "ɖ": 10, "ɖʰ": 11,
        "k": 12, "kʰ": 13, "g": 14, "gʰ": 15,
        "q": 16,
        "tʃ": 17, "tʃʰ": 18, "dʒ": 19, "dʒʰ": 20,
        "f": 21, "s": 22, "z": 23, "ʃ": 24,
        "x": 25, "ɣ": 26, "h": 27, "ʒ": 28,
        "m": 29, "n": 30, "ŋ": 31,
        "l": 32, "r": 33, "ɽ": 34, "j": 35, "w": 36,
        "i": 37, "e": 38, "ɛ": 39, "ɑ": 40, "ə": 41,
        "ɪ": 42, "ʊ": 43, "u": 44, "o": 45, "ɔ": 46,
        "ĩ": 47, "ẽ": 48, "ɑ̃": 49, "ɪ̃": 50, "ʊ̃": 51,
        "ũ": 52, "õ": 53, "ɔ̃": 54,
        "|": 55, "": 56, "": 57,
    }
    vocab = {"": 0}
    idx = 1
    for p in phonemes:
        if p not in vocab:
            vocab[p] = idx
            idx += 1
    return vocab


class UrduG2P:
    def __init__(self):
        self.vocab_dict = build_vocab()
        self.espeak_path = ESPEAK_PATH
        
        if not os.path.exists(self.espeak_path):
            raise FileNotFoundError(f"espeak-ng not found at {self.espeak_path}")
        
        # eSpeak output → our canonical IPA mappings
        # CRITICAL: longer matches must come before shorter ones
        self.mappings = {
            # === eSpeak affricates (must come before single 'c') ===
            'cʰ': 'tʃʰ',    # aspirated ch → tʃʰ
            'c': 'tʃ',      # ch → tʃ  (eSpeak uses 'c' for چ)
            
            # === Aspirated stops ===
            'pʰ': 'pʰ', 'bʰ': 'bʰ', 'tʰ': 'tʰ', 'dʰ': 'dʰ',
            'ʈʰ': 'ʈʰ', 'ɖʰ': 'ɖʰ', 'kʰ': 'kʰ', 'gʰ': 'gʰ',
            
            # === Vowel length + quality ===
            'aː': 'ɑ', 'a': 'ɑ',      # a → ɑ
            'oː': 'o', 'o': 'o',      # o
            'uː': 'u', 'u': 'u',      # u
            'iː': 'i', 'i': 'i',      # i
            'eː': 'e', 'e': 'e',      # e
            
            # === Stress marks: remove ===
            'ˈ': '', 'ˌ': '',
            'ː': '',  # length mark (after specific vowels handled above)
            
            # === Schwa variants ===
            'ʌ': 'ə',
            
            # === Retroflex markers ===
            't.': 'ʈ', 'd.': 'ɖ', 'n.': 'n', 'r.': 'r',
            
            # === Other eSpeak conventions ===
            'A': 'ɑ', 'E': 'ɛ', 'I': 'ɪ', 'O': 'ɔ', 'U': 'ʊ',
            'X': 'x', 'G': 'ɣ', 'N': 'ŋ', 'R': 'ɽ',
        }
        
        # Pre-sort by key length descending for greedy replacement
        self.sorted_mappings = sorted(
            self.mappings.items(),
            key=lambda x: len(x[0]),
            reverse=True
        )
    
    def text_to_phonemes(self, text: str) -> str:
        text = self._normalize(text)
        raw = self._espeak_call(text)
        phonemes = self._postprocess(raw)
        return self._tokenize_to_vocab(phonemes)
    
    def _espeak_call(self, text: str) -> str:
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.txt', delete=False) as f:
            f.write(text)
            temp_path = f.name
        
        try:
            result = subprocess.run(
                [self.espeak_path, "-v", "ur", "-f", temp_path, "--ipa", "-q"],
                capture_output=True, text=True, encoding="utf-8", errors="replace"
            )
            return result.stdout.strip()
        finally:
            os.unlink(temp_path)
    
    def _normalize(self, text: str) -> str:
        text = re.sub(r'[^\u0600-\u06FF\s]', '', text)
        return re.sub(r'\s+', ' ', text).strip()
    
    def _postprocess(self, phonemes: str) -> str:
        """Map eSpeak output to our canonical IPA."""
        for old, new in self.sorted_mappings:
            phonemes = phonemes.replace(old, new)
        return phonemes
    
    def _tokenize_to_vocab(self, phonemes: str) -> str:
        """Tokenize continuous IPA string into space-separated vocab phonemes."""
        multi_char = ['pʰ', 'bʰ', 'tʰ', 'dʰ', 'ʈʰ', 'ɖʰ', 'kʰ', 'gʰ',
                      'tʃʰ', 'dʒʰ', 'tʃ', 'dʒ',
                      'ʃ', 'ʒ', 'ɣ', 'ɽ',
                      'ɑ̃', 'ɪ̃', 'ʊ̃', 'ɔ̃',
                      'ĩ', 'ẽ', 'ũ', 'õ']
        
        tokens = []
        i = 0
        while i < len(phonemes):
            if phonemes[i] == ' ':
                i += 1
                continue
            
            matched = False
            for mc in multi_char:
                end = i + len(mc)
                if end <= len(phonemes) and phonemes[i:end] == mc:
                    tokens.append(mc)
                    i = end
                    matched = True
                    break
            if matched:
                continue
            
            c = phonemes[i]
            if c in self.vocab_dict and c not in ['|', '']:
                tokens.append(c)
            elif c == '|':
                tokens.append('|')
            
            i += 1
        
        return ' '.join(tokens)
    
    def save_vocab(self, path: str = "urdu_phoneme_vocab.json"):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.vocab_dict, f, ensure_ascii=False, indent=2)
        print(f"Vocab saved: {path} ({len(self.vocab_dict)} tokens)")


if __name__ == "__main__":
    g2p = UrduG2P()
    g2p.save_vocab()
    
    test_sentences = ["پاکستان", "اردو", "بچہ", "کتاب", "پانی", "چھوٹی", "بھارت", "کھانا"]
    
    print("\n=== Test Results ===")
    for sent in test_sentences:
        phonemes = g2p.text_to_phonemes(sent)
        print(f"{sent} → {phonemes}")