# Urdu Child Speech Sound Disorder (SSD) Assessment Pipeline

An end-to-end Machine Learning pipeline for automatic speech sound disorder assessment and Goodness-of-Pronunciation (GOP) scoring in Urdu-speaking children.

---

## 🌟 Key Highlights

- **9.47% Test Phoneme Error Rate (PER)** achieved by fine-tuning `IndicWav2Vec-Hindi` on Urdu CTC phonemes (decisively beating XLS-R baseline at 13.21%).
- **Phoneme-First Two-Stage Design**: Combines self-supervised acoustic representations with CTC phoneme recognition for clinical interpretability and data efficiency.
- **Canonical Urdu G2P Engine**: Full Grapheme-to-Phoneme converter for written Urdu covering ~38–44 phonemes (aspirated plosives, retroflex flaps, and nasalized vowels).
- **Logit-Based GOP & Forced Alignment**: Implements `GOP_Margin` and `GOP_MaxLogit` scoring to detect fine-grained phonetic distortions and substitution patterns.

---

## 🏗️ Repository Architecture

```
speech-therapy/
├── g2p/                 # Grapheme-to-Phoneme conversion & IPA phonetic rules
├── data_organization/   # Manifest building, data extraction & dataset processors
├── training/            # Model training & fine-tuning scripts (IndicWav2Vec & XLS-R)
├── testing/             # Goodness-of-Pronunciation (GOP), model evaluation & live checks
├── scraping/            # Web scrapers & dictionary mining utilities
├── manifests/           # CSV manifests and urdu_phoneme_vocab.json
├── documentation/       # Research papers, pipeline specs & architecture guides
├── LICENSE              # MIT License
└── README.md            # Root repository guide
```

---

## 📖 System Pipeline Overview

```
Raw Audio (16kHz Mono)
      │
      ▼
[Stage 0] Front-end Preprocessing (VAD, Normalization, SpecAugment/VTLP)
      │
      ▼
[Stage 1] Self-Supervised Acoustic Backbone (IndicWav2Vec-Hindi / XLS-R)
      │
      ▼
[Stage 2] CTC Phoneme Recognition & Forced Alignment (+ G2P Engine)
      │
      ▼
[Stage 3] Goodness-of-Pronunciation (GOP) & Speech Error Detection
      │  └─► Per-phone output: Correct / Substitution / Deletion / Insertion / Distortion
      ▼
[Stage 4] Hierarchical Speech Disorder Classifier (Pattern Graph & Acoustic Features)
      │  └─► Output: Typical vs. Disorder Category (Articulation, Phonological, CAS, Dysarthria)
      ▼
[Stage 5] Clinical Diagnostic Report & SLP Review Interface
```

For complete technical specifications, see [`documentation/pipeline_architecture_guide.md`](documentation/pipeline_architecture_guide.md).

---

## 🚀 Quick Start Guide

### 1. Installation

```bash
git clone https://github.com/usman-irshad1/speech-therapy.git
cd speech-therapy
pip install torch torchaudio transformers datasets numpy librosa
```

### 2. Dataset Preparation

Download the Mozilla Common Voice Urdu dataset and prepare HuggingFace dataset splits:

```bash
# 1. Download Common Voice Urdu dataset
python data_organization/import_common_voice.py

# 2. Build CSV training manifests with G2P phoneme targets
python data_organization/build_manifest.py

# 3. Create HuggingFace Dataset splits
python data_organization/prepare_datset.py
```

### 3. Model Fine-Tuning

To train Backbone-v1 (`IndicWav2Vec-Hindi` fine-tuned on Urdu CTC phonemes):

```bash
python training/fine_tuning_urdu.py
```

### 4. Running GOP Scoring & Forced Alignment

Run Goodness-of-Pronunciation evaluation on an audio sample with target Urdu text:

```bash
python testing/gop.py --audio "comprehensive_word_audio/پانی.mp3" --text "پانی"
```

To run batch evaluation over the test word corpus:

```bash
python testing/batch_test.py
```

---

## 📚 Documentation Index

- [`documentation/pipeline_architecture_guide.md`](documentation/pipeline_architecture_guide.md) — Comprehensive stage-by-stage architecture guide.
- [`documentation/changelog_and_context.md`](documentation/changelog_and_context.md) — Project refactoring log & context tracker.
- [`documentation/urdu_child_speech_disorder_pipeline.md`](documentation/urdu_child_speech_disorder_pipeline.md) — End-to-end research document.
- [`data/README.md`](data/README.md) — Raw dataset acquisition guide.
- [`cache/README.md`](cache/README.md) — Common Voice dataset download guide.

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).
