# `hf_dataset/` Directory — Processed HuggingFace Dataset Splits

> **Note**: Preprocessed audio arrow files are excluded from Git version control. Follow the instructions below to regenerate the dataset splits.

---

### Dataset Overview

- **Source**: Derived from `manifests/train_manifest.csv`, `dev_manifest.csv`, and `test_manifest.csv`.
- **Target Subdirectories**:
  - `hf_dataset/train/`
  - `hf_dataset/dev/`
  - `hf_dataset/test/`
- **Description**: Contains HuggingFace `Dataset` objects stored on disk with loaded 16kHz audio arrays and mapped Urdu-IPA phoneme target sequences (`labels`).

### How to Regenerate

1. Ensure the Common Voice corpus is downloaded in `cache/`.
2. Generate the CSV manifests:
   ```bash
   python data_organization/build_manifest.py
   ```
3. Convert CSV manifests into the HuggingFace dataset splits:
   ```bash
   python data_organization/prepare_datset.py
   ```
