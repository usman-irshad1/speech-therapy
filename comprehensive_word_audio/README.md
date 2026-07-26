# `comprehensive_word_audio/` Directory — Phoneme Diagnostic Audio Samples

> **Note**: Binary audio files (`.mp3`/`.wav`) are excluded from Git version control.

---

### Overview

This folder contains 35 targeted Urdu word audio recordings used to evaluate and benchmark the Goodness-of-Pronunciation (GOP) scoring and CTC forced-alignment engine across specific Urdu-IPA phonemic contrasts.

### Word Corpus List

The test set covers key phonetic contrasts:
- **Aspirated vs. Unaspirated Plosives**: `پاک` (`p`), `پھول` (`pʰ`), `باب` (`b`), `بھول` (`bʰ`), `کا‌م` (`k`), `کھال` (`kʰ`)
- **Dental vs. Retroflex**: `ٹاٹ` (`ʈ`), `ڈالی` (`ɖ`), `ڈھکن` (`ɖʰ`), `ٹھیکہ` (`ʈʰ`), `آڑو` (`ɽ`), `باڑھ` (`ɽʰ`)
- **Fricatives & Affricates**: `فال` (`f`), `خام` (`x`), `غالب` (`ɣ`), `چپ` (`tʃ`), `چھال` (`tʃʰ`), `جام` (`dʒ`), `جھاڑو` (`dʒʰ`), `شام` (`ʃ`)
- **Nasalization**: `جاں`, `یوں`, `منہ`

### Running Batch Evaluation

To evaluate GOP scores on this audio suite, run:

```bash
python testing/batch_test.py
```
