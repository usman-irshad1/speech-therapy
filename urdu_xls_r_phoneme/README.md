# `urdu_xls_r_phoneme/` — Model Checkpoint (XLS-R Baseline)

> **Note**: Model weights and pytorch binary files are excluded from Git version control.

---

### Model Details

- **Base Architecture**: `facebook/wav2vec2-xls-r-300m`
- **Fine-Tuning Target**: Urdu CTC Phoneme Recognition
- **Performance**: 13.21% Phoneme Error Rate (PER) on held-out test split.

### How to Re-Train

To fine-tune XLS-R 300M on the Urdu phoneme dataset:

```bash
python training/fine_tuning_train.py
```
