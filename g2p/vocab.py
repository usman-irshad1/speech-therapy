
import json
# Canonical Urdu-IPA phoneme inventory (~41 phonemes)
# Based on: PronouncUR (Sarfraz et al. 2018), CLE (Saleem et al. 2002), Hussain (2004)
# Corrections applied: /ɳ/ excluded (allophone, not phonemic), /ʒ/ included as marginal
urdu_phonemes = {
    # === Plosives (unaspirated + aspirated) ===
    "p": 0, "pʰ": 1,
    "b": 2, "bʰ": 3,
    "t": 4, "tʰ": 5,
    "d": 6, "dʰ": 7,
    "ʈ": 8, "ʈʰ": 9,
    "ɖ": 10, "ɖʰ": 11,
    "k": 12, "kʰ": 13,
    "g": 14, "gʰ": 15,
    "q": 16,  # Perso-Arabic loan, uvular
    
    # === Affricates ===
    "tʃ": 17, "tʃʰ": 18,
    "dʒ": 19, "dʒʰ": 20,
    
    # === Fricatives ===
    "f": 21,
    "s": 22,
    "z": 23,
    "ʃ": 24,
    "x": 25,   # Perso-Arabic loan
    "ɣ": 26,   # Perso-Arabic loan
    "h": 27,
    "ʒ": 28,   # Marginal — verify with linguist before freezing
    
    # === Nasals ===
    "m": 29,
    "n": 30,
    "ŋ": 31,
    
    # === Liquids/Glides ===
    "l": 32,
    "r": 33,
    "ɽ": 34,   # Retroflex flap
    "j": 35,
    "w": 36,
    
    # === Oral Vowels ===
    "i": 37, "e": 38, "ɛ": 39,
    "ɑ": 40, "ə": 41,
    "ɪ": 42, "ʊ": 43,
    "u": 44, "o": 45, "ɔ": 46,
    
    # === Nasalized Vowels ===
    "ĩ": 47, "ẽ": 48, "ɑ̃": 49,
    "ɪ̃": 50, "ʊ̃": 51, "ũ": 52,
    "õ": 53, "ɔ̃": 54,
    
    # === Special CTC tokens ===
    "|": 55,        # Word delimiter (replaces spaces)
    "": 56,         # CTC blank token (pad)
    "": 57,         # Padding token
}

# IMPORTANT: The CTC blank token is index 0 in the CTC algorithm itself,
# but in the tokenizer vocab we use "" as the pad token.
# Wav2Vec2CTCTokenizer handles the blank token internally.

# Rebuild with proper ordering: blank first for CTC convention
vocab_dict = {"": 0}  # CTC blank token MUST be index 0
idx = 1
for phone in urdu_phonemes:
    if phone not in vocab_dict:
        vocab_dict[phone] = idx
        idx += 1

with open("urdu_phoneme_vocab.json", "w", encoding="utf-8") as f:
    json.dump(vocab_dict, f, ensure_ascii=False, indent=2)

print(f"Vocabulary size: {len(vocab_dict)} phonemes")
print(f"Saved to urdu_phoneme_vocab.json")