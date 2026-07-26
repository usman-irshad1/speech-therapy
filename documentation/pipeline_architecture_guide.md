# Pipeline Architecture Guide: Urdu Child Speech Sound Disorder (SSD) Assessment

> **Reference Document**: Detailed breakdown of the multi-stage machine learning architecture implemented in this repository, based on [`urdu_child_speech_disorder_pipeline.md`](file:///C:/Users/usman/Desktop/spech_pipeline/documentation/urdu_child_speech_disorder_pipeline.md) and [`urdu_pipeline_docA_research_design.md`](file:///C:/Users/usman/Desktop/spech_pipeline/documentation/urdu_pipeline_docA_research_design.md).

---

## 1. High-Level System Architecture

The project follows a **two-stage, phoneme-first pipeline design** rather than a single black-box audio-to-disorder classifier. 

### Why Phoneme-First?
1. **Clinical Interpretability**: Speech-Language Pathologists (SLPs) require phone-level evidence (substitutions, distortions, deletions) to diagnose and target therapy.
2. **Data Efficiency**: Low-resource Urdu disorder data can be bootstrapped from adult Urdu ASR + Hindi phonetic cross-lingual transfer, requiring far fewer labeled child disorder samples.

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

---

## 2. Detailed Breakdown of Each Stage

---

### Stage 0: Front-End Preprocessing & Augmentation
* **Input**: Raw microphone recording or audio clip.
* **Operation**:
  - **Voice Activity Detection (VAD)**: Trims leading and trailing silence.
  - **Resampling & Normalization**: Converts input audio to 16kHz mono PCM waveform.
  - **Child-Specific Augmentation (during training)**: Applies Vocal Tract Length Perturbation (VTLP) and pitch shifting to bridge the acoustic gap between adult pretraining data and child speech.
* **Module Location**: [`data_organization/`](file:///C:/Users/usman/Desktop/spech_pipeline/data_organization)

---

### Stage 1: Self-Supervised Acoustic Backbone
* **Input**: 16kHz preprocessed audio waveform.
* **Operation**:
  - Leverages pre-trained self-supervised CNN + Transformer representations (`IndicWav2Vec-Hindi` or `XLS-R 300M`).
  - Converts raw audio into frame-level dense acoustic embeddings (sampled every 20ms).
  - **Current Model Status**: `IndicWav2Vec-Hindi` fine-tuned on Urdu achieves **9.47% Phoneme Error Rate (PER)**.
* **Model Checkpoint**: [`urdu_indicwav2vec_hindi_phoneme/`](file:///C:/Users/usman/Desktop/spech_pipeline/urdu_indicwav2vec_hindi_phoneme)
* **Script**: [`training/fine_tuning_urdu.py`](file:///C:/Users/usman/Desktop/spech_pipeline/training/fine_tuning_urdu.py)

---

### Stage 2: CTC Phoneme Recognition & Forced Alignment
* **Input**: Frame-level acoustic representations from Stage 1 + Expected target text/prompt.
* **Operation**:
  1. **G2P Conversion**: The Urdu G2P engine converts written target words (e.g. `"پانی"`) into canonical IPA phoneme strings (e.g. `"p ɑː n iː"`).
  2. **Phoneme Recognition Head**: CTC output projection layer maps acoustic representations to posterior distributions over the 38–44 canonical Urdu-IPA phonemes (including aspirated plosives `/pʰ, bʰ, tʰ, dʰ, ʈʰ, ɖʰ, kʰ, gʰ/`, retroflex flaps `/ɽ/`, and nasalized vowels).
  3. **CTC Forced Alignment**: Viterbi forced alignment computes time boundaries (start & end timestamps) for each expected phoneme in the audio sequence.
* **Module Locations**: 
  - G2P: [`g2p/urdug2p.py`](file:///C:/Users/usman/Desktop/spech_pipeline/g2p/urdug2p.py)
  - Aligner: [`testing/gop.py`](file:///C:/Users/usman/Desktop/spech_pipeline/testing/gop.py)

---

### Stage 3: Goodness-of-Pronunciation (GOP) & Speech Error Detection
* **Input**: Time-aligned CTC frame posteriors + expected phoneme sequence.
* **Operation**:
  - **Logit-Based GOP Scoring**: Calculates `GOP_Margin` (log-likelihood difference between target phone and top competitor) and `GOP_MaxLogit` over aligned frames.
  - **Distortion Detection**: Continuous GOP score flags "close-but-imperfect" pronunciations (distortions) that edit-distance metrics miss.
  - **Substitution & Insertion/Deletion Typing**: Uses Levenshtein alignment and phoneme confusion matrices to identify specific sound swaps (e.g., retroflex replacement `/ɽ/` → `/r/`, or dropped aspiration `/pʰ/` → `/p/`).
* **Per-Phone Output**: Category label per target phone:
  - `Correct`
  - `Substitution` (with substitute phone ID)
  - `Deletion`
  - `Insertion`
  - `Distortion` (with severity score)
* **Script**: [`testing/gop.py`](file:///C:/Users/usman/Desktop/spech_pipeline/testing/gop.py)

---

### Stage 4: Speech Disorder Classification
* **Input**: Per-phone error pattern sequence + error consistency metrics across repeated prompt attempts + prosodic/acoustic features.
* **Operation**:
  - **Hierarchical Classification**:
    1. *Step 4a*: Binary screener — Typically Developing vs. Speech Sound Disordered.
    2. *Step 4b*: Motor execution vs. Linguistic/Phonological branch split.
    3. *Step 4c*: Fine-grained category assignment.
* **Clinical Categories**:
  - **Articulation Disorder**: Isolated motor production errors on specific phones.
  - **Phonological Disorder / Delay**: Consistent rule-based error patterns (e.g., fronting, stopping, cluster reduction).
  - **Childhood Apraxia of Speech (CAS)**: Highly inconsistent error patterns across repeated attempts of the same target word.
  - **Dysarthria**: Motor speech disorder characterized by prosodic, rate, and voice quality disturbances alongside articulation errors.

---

### Stage 5: Clinical Diagnostic Report & SLP Interface
* **Input**: Outputs from Stage 3 & Stage 4.
* **Operation**:
  - Generates an interpretable diagnostic report for clinicians:
    - **PCC Score**: Percentage of Consonants Correct.
    - **Phoneme Error Map**: Visual breakdown of targeted vs. produced phones across word positions (initial, medial, final).
    - **Disorder Risk Profile**: Likelihood scores per clinical category with confidence bounds.
    - **Low-Confidence Flags**: Highlights ambiguous audio segments for human SLP review.

---

## 3. Summary of Repository Script Mapping

| Stage | Script Path | Main Function |
|---|---|---|
| **Data Scraping** | [`scraping/scrapper.py`](file:///C:/Users/usman/Desktop/spech_pipeline/scraping/scrapper.py) | Scrapes dictionary words and audio clips |
| **G2P Engine** | [`g2p/urdug2p.py`](file:///C:/Users/usman/Desktop/spech_pipeline/g2p/urdug2p.py) | Converts Urdu script to IPA phoneme sequences |
| **Dataset Prep** | [`data_organization/build_manifest.py`](file:///C:/Users/usman/Desktop/spech_pipeline/data_organization/build_manifest.py) | Builds CSV manifests with phoneme targets |
| **Model Training** | [`training/fine_tuning_urdu.py`](file:///C:/Users/usman/Desktop/spech_pipeline/training/fine_tuning_urdu.py) | Fine-tunes IndicWav2Vec-Hindi on Urdu phonemes |
| **Evaluation** | [`testing/test_model.py`](file:///C:/Users/usman/Desktop/spech_pipeline/testing/test_model.py) | Evaluates Phoneme Error Rate (PER) |
| **Forced Alignment & GOP** | [`testing/gop.py`](file:///C:/Users/usman/Desktop/spech_pipeline/testing/gop.py) | Computes CTC forced alignment and GOP scores |
| **Batch Diagnostic** | [`testing/batch_test.py`](file:///C:/Users/usman/Desktop/spech_pipeline/testing/batch_test.py) | Batch GOP evaluation on corpus recordings |
