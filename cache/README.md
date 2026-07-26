# `cache/` Directory — Cached Raw Audio Corpora

> **Note**: Cached raw audio files and dataset archives are excluded from Git version control. Follow the instructions below to download and rebuild the cache.

---

### Dataset: Mozilla Common Voice Urdu

- **Source**: Mozilla Common Voice Urdu Corpus (v1 / Kaggle `cookiefinder/mozilla-common-voice-urdu`)
- **Target Path**: `cache/datasets/cookiefinder/mozilla-common-voice-urdu`
- **Description**: Crowd-sourced adult Urdu speech dataset containing validated audio clips (`clips/*.mp3`) and TSV metadata manifests (`train.tsv`, `dev.tsv`, `test.tsv`, `validated.tsv`). This serves as the core training dataset for the phoneme-level CTC model.

### How to Download

To download the Common Voice Urdu dataset via KaggleHub, run:

```bash
python data_organization/import_common_voice.py
```

This script executes:
```python
import kagglehub

path = kagglehub.dataset_download("cookiefinder/mozilla-common-voice-urdu")
print("Downloaded Common Voice Urdu to:", path)
```
