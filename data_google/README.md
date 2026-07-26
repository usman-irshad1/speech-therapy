# `data_google/` Directory — Google FLEURS Urdu Dataset

> **Note**: Dataset binaries are excluded from Git version control to keep the repository lightweight. Follow the instructions below to re-download or recreate this dataset.

---

### Dataset: Google FLEURS Urdu (`ur_pk`)

- **Source**: Google FLEURS Multilingual Speech Dataset (`google/fleurs`)
- **Target Path**: `data_google/google_fleurs_ur`
- **Description**: High-quality parallel read speech dataset for Urdu (`ur_pk` locale) released by Google, containing audio samples with sentence-level transcripts.

### How to Re-Download

To download and populate this folder, run:

```bash
python data_organization/google_dataset.py
```

This script executes:
```python
from datasets import load_dataset

fleurs = load_dataset("google/fleurs", "ur_pk")
fleurs.save_to_disk("data_google/google_fleurs_ur")
```
