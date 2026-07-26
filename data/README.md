# `data/` Directory — Downloaded Raw Datasets

> **Note**: Dataset binaries are excluded from Git version control to keep the repository lightweight. Follow the instructions below to re-download or recreate this dataset.

---

### Dataset: IndicSUPERB (Kathbath Urdu)

- **Source**: AI4Bharat Kathbath Urdu Speech Corpus (`ai4bharat/Kathbath`)
- **Target Path**: `data/indic_superb_urdu`
- **Description**: Standardized Urdu read-speech dataset from the IndicSUPERB benchmark suite, providing natural adult spoken Urdu audio clips and orthographic transcripts.

### How to Re-Download

To download and populate this folder, run:

```bash
python data_organization/khattab_data_set.py
```

This script executes:
```python
from datasets import load_dataset

dataset = load_dataset("ai4bharat/Kathbath", "urdu")
dataset.save_to_disk("data/indic_superb_urdu")
```
