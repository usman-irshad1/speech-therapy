# `urdu_indicwav2vec_hindi_phoneme/` — Model Checkpoint (Backbone-v1)

> **Note**: Model weights and pytorch binary files (`model.safetensors`, `pytorch_model.bin`) are excluded from Git version control.

---

### Model Details

- **Base Architecture**: `ai4bharat/indicwav2vec_v1_hindi`
- **Fine-Tuning Target**: Urdu CTC Phoneme Recognition
- **Performance**: **9.47% Phoneme Error Rate (PER)** on held-out test split (Primary Backbone-v1 Winner).
- **Contents**: Fine-tuned Wav2Vec2 weights, preprocessor config, and feature extractor configuration.

### How to Re-Train

To fine-tune this model from scratch:

```bash
python training/fine_tuning_urdu.py
```
