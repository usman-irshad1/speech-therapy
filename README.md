# Urdu Phoneme Recognition & Goodness-of-Pronunciation (GOP) Assessment Pipeline

[![Python](https://img.shields.io/badge/Python-3.9%2B%20%7C%20PyTorch-blue?style=flat-square)]()
[![Backbone](https://img.shields.io/badge/Backbone-IndicWav2Vec--Hindi%20%7C%20XLS--R-orange?style=flat-square)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](LICENSE)

An end-to-end **Urdu Phoneme Recognition, Forced Alignment, and Goodness-of-Pronunciation (GOP) research pipeline** built with PyTorch and self-supervised Wav2Vec2 acoustic backbones, designed as an acoustic front-end toward automated Speech Sound Disorder (SSD) screening.

> **Clinical Validation & Dataset Disclaimer:**  
> This repository is an **academic and engineering research prototype** and is **not a clinically validated medical diagnostic device**.  
> - **Acoustic Model Training & Test PER (`9.47%`)**: Trained and evaluated on adult read-speech utterances from **Mozilla Common Voice Urdu** mapped to canonical IPA phoneme sequences via our deterministic Urdu G2P engine.  
> - **GOP & Pronouncing Assessment (`testing/gop.py`)**: Evaluates per-phoneme frame posteriors (`GOP_Margin`, `GOP_MaxLogit`) on target Urdu word recordings (`comprehensive_word_audio/`). Deployment for pediatric clinical speech-language pathology requires future validation on annotated child speech-disorder corpora under qualified Speech-Language Pathologist (SLP) supervision.

---

## 🌟 Key Technical Highlights

- **9.47% Test Phoneme Error Rate (PER) on Common Voice Urdu**: Achieved by fine-tuning `IndicWav2Vec-Hindi` with a CTC phoneme head over a 44-symbol Urdu IPA vocabulary (improving over the multilingual `XLS-R-300M` baseline at `13.21%` PER on the same split).
- **Phoneme-First Two-Stage Architecture**: Decouples self-supervised frame-level acoustic representations from rule-based Urdu Grapheme-to-Phoneme (G2P) targets for phoneme-level interpretability.
- **Canonical Urdu G2P Engine (`g2p/`)**: Deterministic converter for written Urdu script covering ~38–44 IPA phonemes (aspirated plosives, retroflex stops/flaps, uvulars, and nasalized vowels).
- **Logit-Based GOP & CTC Forced Alignment (`testing/gop.py`)**: Computes frame-aligned `GOP_Margin` (target vs. best competing phoneme logit margin) and `GOP_MaxLogit` scores to flag phoneme substitutions, deletions, and distortions.

---

## 📊 Dataset Provenance, Splits & Evaluation Methodology

| Evaluation Component | Dataset Source | Split / Corpus Details | Metric & Observed Result |
| :--- | :--- | :--- | :--- |
| **Stage 1–2: CTC Phoneme Recognition** | **Mozilla Common Voice Urdu** (`data_organization/import_common_voice.py`) | Standard train / validation / held-out test splits built via `build_manifest.py` & `prepare_datset.py` with G2P IPA targets (`urdu_phoneme_vocab.json`). | **Test PER: `9.47%`** (`IndicWav2Vec-Hindi`) vs. **`13.21%`** (`XLS-R`) |
| **Stage 3: Word-Level GOP Scoring** | **Curated Urdu Word Audio Corpus** (`comprehensive_word_audio/` & `test_batch/`) | Target single-word Urdu recordings evaluated against canonical G2P phoneme transcriptions via CTC forced alignment. | Per-phoneme `GOP_Margin` & `GOP_MaxLogit` confidence scores |
| **Stage 4–5: Disorder Taxonomy (Design Spec)** | Architectural specification (`documentation/urdu_child_speech_disorder_pipeline.md`) | Rule/graph-based error pattern aggregation (Articulation, Phonological, CAS, Dysarthria). | Architectural design & research specification (pending clinical pediatric corpus) |

---

## 🏗️ Repository Architecture

```text
speech-therapy/
├── g2p/                              # Urdu Grapheme-to-Phoneme (G2P) rules & CISAMPA-to-IPA converter
├── data_organization/                # Common Voice Urdu importer, CSV manifest builder & HF dataset prep
├── training/                         # CTC phoneme fine-tuning scripts (IndicWav2Vec-Hindi & XLS-R)
├── testing/                          # Goodness-of-Pronunciation (GOP) forced alignment & batch evaluation
├── comprehensive_word_audio/         # Reference Urdu word audio samples for GOP testing
├── manifests/                        # Generated CSV manifests and phoneme vocabulary mappings
├── documentation/                    # Stage-by-stage architecture guides and research specifications
├── urdu_phoneme_vocab.json           # 44-token Urdu IPA CTC vocabulary dictionary
├── LICENSE                           # MIT License
└── README.md                         # Root repository documentation
```

---

## 📖 System Pipeline Overview

```text
Raw Audio (16kHz Mono)
      │
      ▼
[Stage 0] Front-end Preprocessing (VAD, Normalization, SpecAugment)
      │
      ▼
[Stage 1] Self-Supervised Acoustic Backbone (IndicWav2Vec-Hindi / XLS-R)
      │
      ▼
[Stage 2] CTC Phoneme Recognition & Forced Alignment (+ Canonical Urdu G2P Engine)
      │   └──► Evaluated on Mozilla Common Voice Urdu (9.47% Test PER)
      ▼
[Stage 3] Goodness-of-Pronunciation (GOP) & Phoneme Error Detection (testing/gop.py)
      │   └──► Per-phoneme output: GOP_Margin / GOP_MaxLogit (Correct vs. Substitution / Deletion)
      ▼
[Stage 4–5] Clinical Error Pattern Aggregation & Diagnostic Report Specification
```

For full architectural specifications, see [`documentation/pipeline_architecture_guide.md`](documentation/pipeline_architecture_guide.md).

---

## 🚀 Quick Start Guide

### 1. Installation

```bash
git clone https://github.com/usman-irshad1/speech-therapy.git
cd speech-therapy
pip install torch torchaudio transformers datasets numpy librosa
```

### 2. Dataset Preparation (Common Voice Urdu ASR Splits)

```bash
# 1. Import Mozilla Common Voice Urdu audio and transcripts
python data_organization/import_common_voice.py

# 2. Convert Urdu script transcripts to IPA phoneme sequences via G2P and build CSV manifests
python data_organization/build_manifest.py

# 3. Package train / validation / test HuggingFace Dataset splits
python data_organization/prepare_datset.py
```

### 3. Acoustic Model Fine-Tuning

To fine-tune `IndicWav2Vec-Hindi` on the Urdu CTC phoneme splits:

```bash
python training/fine_tuning_urdu.py
```

### 4. Running GOP Scoring & Forced Alignment

Evaluate per-phoneme Goodness-of-Pronunciation on a target Urdu word recording:

```bash
python testing/gop.py --audio "comprehensive_word_audio/پانی.mp3" --text "پانی"
```

To run batch GOP evaluation across the word test suite:

```bash
python testing/batch_test.py
```

---

## 📚 Documentation Index

- [`documentation/pipeline_architecture_guide.md`](documentation/pipeline_architecture_guide.md) — Stage-by-stage acoustic and GOP architecture guide.
- [`documentation/changelog_and_context.md`](documentation/changelog_and_context.md) — Experimental log comparing `IndicWav2Vec-Hindi` (`9.47%` PER) and `XLS-R` (`13.21%` PER).
- [`documentation/urdu_child_speech_disorder_pipeline.md`](documentation/urdu_child_speech_disorder_pipeline.md) — Research specification for extending CTC/GOP outputs to pediatric speech sound disorder classification.
- [`data/README.md`](data/README.md) — Dataset directory notes.
- [`cache/README.md`](cache/README.md) — HuggingFace / Common Voice cache notes.

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).
