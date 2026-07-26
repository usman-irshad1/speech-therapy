# Project Session Log & Architecture Context

> **Agent Guideline**: Update this file after key structural or architectural changes and read it at the start of work sessions to preserve project context.

---

## 1. Project Overview & Current Architecture State

- **Goal**: End-to-end ML pipeline for Automatic Speech Sound Disorder (SSD) Assessment in Urdu-speaking children.
- **Pipeline Architecture**: Two-stage, phoneme-first pipeline:
  1. **Acoustic Backbone**: `IndicWav2Vec-Hindi` fine-tuned on Urdu phonemes (**9.47% test PER** vs XLS-R's 13.21%). Model checkpoint: `urdu_indicwav2vec_hindi_phoneme/`.
  2. **G2P Engine**: Canonical Urdu-IPA inventory (~38–44 phonemes including aspirated plosives, retroflex flaps, and nasalized vowels). Located in `g2p/`.
  3. **Forced Alignment & Goodness-of-Pronunciation (GOP)**: Logit-based GOP scoring engine (`GOP_Margin` and `GOP_MaxLogit`) located in `testing/gop.py`.
  4. **Disorder Classifier (Stage 4)**: Sequence/graph classifier over GOP error signatures and prosodic features.

---

## 2. Refactoring & Restructuring Log

### [2026-07-26] Codebase Reorganization into Modular Packages

Reorganized all 25 root Python scripts into 5 domain-specific subdirectories with `__init__.py` module support and resilient import paths (`sys.path` fallback):

| Subdirectory | Contained Scripts | Description |
|---|---|---|
| [`g2p/`](file:///C:/Users/usman/Desktop/spech_pipeline/g2p) | `urdug2p.py`, `Urdu_to_IPA.py`, `urdu_g2p_patches.py`, `vocab.py` | Urdu grapheme-to-phoneme conversion, IPA mappings, vocabulary definitions, and overrides. |
| [`scraping/`](file:///C:/Users/usman/Desktop/spech_pipeline/scraping) | `scrapper.py`, `data_mining.py`, `gen_words.py`, `check_download.py` | Web scraping, data mining for dictionary/audio data, and word generation. |
| [`data_organization/`](file:///C:/Users/usman/Desktop/spech_pipeline/data_organization) | `build_manifest.py`, `prepare_datset.py`, `import_common_voice.py`, `google_dataset.py`, `khattab_data_set.py`, `download_tester_data.py`, `extract.py`, `processor.py` | CSV manifest generation, HuggingFace dataset preparation, data extraction, and custom Wav2Vec2 processors. |
| [`training/`](file:///C:/Users/usman/Desktop/spech_pipeline/training) | `train.py`, `fine_tuning_train.py`, `fine_tuning_urdu.py` | Model fine-tuning and training scripts for IndicWav2Vec and XLS-R backbones. |
| [`testing/`](file:///C:/Users/usman/Desktop/spech_pipeline/testing) | `gop.py`, `test_model.py`, `batch_test.py`, `coverage_test.py`, `live_check.py`, `debug.py` | Model evaluation, batch testing, GOP forced-alignment scoring, phoneme coverage audit, and live audio checks. |

### Script Import Adjustments
- Updated `gop.py` default model directory to point to `urdu_indicwav2vec_hindi_phoneme` with automatic fallback to `urdu_xls_r_phoneme`.
- Added `PROJECT_ROOT` path injection and `try/except` imports in `build_manifest.py`, `gop.py`, `batch_test.py`, `coverage_test.py`, and `debug.py` to allow standalone execution (`python testing/gop.py`) or package imports (`from testing.gop import ...`).

---

## 3. Core Documentation Index

- [`pipeline_architecture_guide.md`](file:///C:/Users/usman/Desktop/spech_pipeline/documentation/pipeline_architecture_guide.md) — Step-by-step breakdown of the multi-stage research pipeline architecture.
- [`urdu_child_speech_disorder_pipeline.md`](file:///C:/Users/usman/Desktop/spech_pipeline/documentation/urdu_child_speech_disorder_pipeline.md) — Comprehensive end-to-end technical report.
- [`urdu_pipeline_docA_research_design.md`](file:///C:/Users/usman/Desktop/spech_pipeline/documentation/urdu_pipeline_docA_research_design.md) — Research foundation, transfer learning strategy, & clinical background.
- [`urdu_pipeline_docB_g2p_engineering.md`](file:///C:/Users/usman/Desktop/spech_pipeline/documentation/urdu_pipeline_docB_g2p_engineering.md) — Phoneme inventory, Hindi-to-Urdu mappings, and G2P engineering saga.
- [`urdu_pipeline_docC_training_engineering.md`](file:///C:/Users/usman/Desktop/spech_pipeline/documentation/urdu_pipeline_docC_training_engineering.md) — Training benchmarks and model comparative analysis.
- [`urdu_pipeline_docD_roadmap.md`](file:///C:/Users/usman/Desktop/spech_pipeline/documentation/urdu_pipeline_docD_roadmap.md) — Project roadmap & risk matrix.
- [`urdu_pipeline_next_steps_plan.md`](file:///C:/Users/usman/Desktop/spech_pipeline/documentation/urdu_pipeline_next_steps_plan.md) — Priority action plan.

---

## 4. Immediate Next Steps

1. **GOP Verification**: Run GOP scoring on deliberate mispronunciation recordings (`testing/gop.py` / `testing/batch_test.py`).
2. **Elicitation List**: Design phonemically-balanced Urdu elicitation word list covering retroflex, aspirated, and nasalized contrasts.
3. **Outreach & Data Collection**: Initiate contact with speech-language therapy clinics for Urdu child speech data gathering.
