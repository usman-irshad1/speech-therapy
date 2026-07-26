# Doc A — Research Foundation & System Design
### Urdu Child Speech-Disorder Assessment Pipeline (1 of 4)

*This is one of four documents split from the original comprehensive pipeline report. This one covers the "why": model architecture choice, error-detection theory, disorder classification theory, transfer learning strategy, datasets, augmentation, evaluation, and deployment. See the companion documents for G2P engineering (Doc B), model training engineering (Doc C), and the project roadmap (Doc D).*

---

# An End-to-End ML Pipeline for Automatic Speech Sound Disorder Assessment in Urdu-Speaking Children

## 0. Framing the problem honestly

Before the architecture: two constraints shape every downstream decision.

1. **UltraSuite is English, not Urdu.** UltraSuite (Eshky et al., 2018) contains ~18.7 hours of ultrasound + acoustic data from 86 English-speaking children (58 typically developing + 28 with SSDs), used for tongue-imaging and forced-alignment research, and the strongest published phoneme-recognition result on it (PER 0.15, F1 82%) used wav2vec 2.0 fine-tuned on English. It has no Urdu content and no ultrasound-free Urdu equivalent exists. Its practical role in your project is as a **methodology template** (forced-alignment pipeline, error-detection formulation, evaluation protocol) and as **English pretraining/validation data for the ASR backbone**, not as Urdu training data.
2. **No public Urdu child speech-disorder corpus exists.** Every dataset in Section 7 is either (a) Urdu but adult/read-speech, or (b) child speech-disorder but not Urdu. Data collection is not optional polish here — it is the critical path. Plan the ML architecture around this reality: maximum transfer from related resources, minimum reliance on a large labeled Urdu-SSD set.

With that grounded, here is the full pipeline.

---

## 1. Overall Architecture

### The core building blocks, compared

| Approach | What it does | Fit for this task |
|---|---|---|
| **Wav2Vec 2.0 / XLSR-53** | Self-supervised CNN+Transformer encoder, CTC fine-tuning | Strong general-purpose backbone; XLSR-53's 53-language pretraining includes Urdu-adjacent phonetics |
| **XLS-R (300M/1B/2B)** | Wav2Vec2 scaled to 128 languages, ~436k hours | **Best default choice.** Explicitly pretrained on Urdu (via CommonVoice/VoxPopuli-adjacent multilingual data) and on Hindi, Punjabi, Sanskrit — the same phonetic cluster as Urdu, confirmed by codebook-clustering studies |
| **HuBERT** | Self-supervised via masked cluster prediction (iterative k-means) rather than contrastive loss | Comparable phoneme-discrimination quality to wav2vec2; fewer readily available Urdu-adjacent checkpoints than XLS-R/MMS |
| **MMS (Massively Multilingual Speech)** | Wav2vec2-style pretraining across 1,000+ languages including Urdu | Excellent breadth; use as a second candidate backbone or for zero-shot phoneme recognition when Urdu fine-tuning data is scarce |
| **Whisper** | Encoder-decoder, weakly-supervised on 680k hours, trained for text (not phoneme) output | Good for general Urdu transcription (there are decent community fine-tunes), but Whisper's BPE-text decoding and hallucination tendency on short/disfluent/child/disordered speech make it a **poor primary choice for phoneme-level error detection**. Use only as an auxiliary sanity-check ASR or for word-level context. |
| **SeamlessM4T** | Multilingual, multitask (ASR/S2T/S2S) encoder-decoder | Broad language coverage including Urdu, but designed for translation/transcription, not phoneme-level clinical scoring; heavier, less transparent at the phoneme layer |
| **Conformer / RNN-T** | Convolution-augmented Transformer, streaming-friendly | Better suited to production-scale ASR teams with large labeled data; for a low-resource clinical task, self-supervised wav2vec2-family models generalize better from little labeled data |
| **CTC-based phoneme recognition** | Frame-level classification + CTC collapse, no autoregression | **This is the actual output head you want**, on top of a self-supervised encoder — CTC posteriors are exactly what Goodness-of-Pronunciation (GOP) scoring needs |
| **G2P (grapheme-to-phoneme)** | Converts target/reference text to expected phoneme sequence | Required to generate the "expected" side of every substitution/deletion/insertion comparison |
| **Forced alignment** | Aligns audio to a known/expected phoneme sequence in time | Needed for GOP, for word/phone-level scoring, and for segment-level features feeding disorder classification |
| **GOP (Goodness of Pronunciation)** | Posterior-probability-based scoring of how well a produced phone matches the expected phone | The most clinically interpretable and best-validated method for disordered/L2 speech scoring; works directly off CTC/DNN posteriors |
| **MDD (Mispronunciation Detection & Diagnosis)** | The task family that outputs *what* was mispronounced, not just *that* it was | This is literally your Section 3–4 problem statement; the field has ~5 years of directly relevant architectures (below) |

### Recommended architecture

A **two-stage, phoneme-first pipeline**, not an end-to-end audio→disorder-label model:

```
Raw audio (16kHz)
   │
   ▼
[Stage 0] Front-end: VAD, denoising, child-speech-tuned SpecAugment
   │
   ▼
[Stage 1] Self-supervised encoder: XLS-R (or MMS) — frozen/partially fine-tuned
   │
   ▼
[Stage 2] CTC phoneme-recognition head, Urdu phoneme inventory
   │         + forced alignment against the expected phoneme sequence
   │         (from G2P on the elicited word/prompt)
   ▼
[Stage 3] GOP + confusion-matrix + sequence-alignment error detector
   │         → per-phone labels: correct / substitution / deletion / insertion / distortion
   ▼
[Stage 4] Sequence/graph classifier over the error pattern + acoustic embeddings
   │         → disorder category (articulation / phonological / CAS / dysarthria / delay)
   ▼
Interpretable report: phoneme-level error map + disorder likelihood + confidence
```

**Why not one end-to-end audio→disorder classifier?** Three reasons, all evidence-based: (1) clinicians need phoneme-level evidence to trust and act on the output — a black-box label is not deployable in a diagnostic device; (2) end-to-end classifiers need far more labeled disorder examples than will exist for Urdu for years, whereas the phoneme-recognition stage can be bootstrapped from Urdu ASR data (which exists) plus cross-lingual transfer; (3) the MDD/GOP literature consistently frames pronunciation assessment as phoneme-first pipelines even in high-resource languages (English MDD, e.g. Peng et al. 2021 wav2vec2-MDD, Wu et al. 2021 transformer end-to-end MDD, Ye et al. 2022 APL-embeddings), specifically because interpretability and label-efficiency both favor decomposing the task.

---

## 3. Speech Error Detection

| Method | What it captures | Where it fits |
|---|---|---|
| **Edit distance (Levenshtein) between predicted and expected phoneme sequences** | Sub/del/ins counts at sequence level | Cheap baseline; good for aggregate PER-style metrics, weak for distortion (a "close but wrong" phone is scored the same as a wildly wrong one) |
| **Phoneme confusion matrices** | Which phones get swapped for which, in aggregate | Essential clinical artifact — this *is* the substitution-error diagnosis (e.g., /s/→/θ/ patterns), and it's how you'll validate the system against known Urdu child phonology error patterns |
| **Alignment-based methods (forced alignment + frame posteriors)** | Precise timing + likelihood of each expected phone being realized | Backbone for GOP and for locating deletions/insertions in time, not just in sequence |
| **GOP scoring** | Per-phone posterior-probability-based "goodness," originally DNN-HMM, now computed directly from CTC/attention posteriors | **Primary distortion detector.** Distortions are the hardest error type for edit-distance methods (the phone isn't cleanly substituted, it's produced imperfectly) — GOP's continuous score is what lets you flag "correct category, poor execution" rather than forcing a binary correct/wrong call. Recent work applies logit-based GOP directly to self-supervised model outputs and shows this outperforms classic DNN-HMM GOP for detecting non-native/disordered segmental errors; GOP has also been validated directly on clinically disordered speech (unilateral facial palsy patients), where higher GOP-deviance scores correlated with clinician-rated severity |
| **Transformer classifiers (frame- or phone-level)** | Learned end-to-end error/no-error or error-type labels | Best when you have enough labeled disordered data to supervise directly; combine with GOP as an auxiliary feature rather than replacing it, given data scarcity |
| **Sequence labeling (CTC-alignment-based joint models)** | Joint "predict what was said AND whether it matches" | Wu et al. (2021) transformer-based end-to-end MDD and Peng et al. (2021) wav2vec2 fine-tuned MDD are the closest published architectures to what you need — both frame MDD as sequence labeling over the aligned target/actual phone pair, with reported gains from wav2vec2 features over earlier DNN-HMM systems |

**Recommended stack**: forced alignment → per-phone GOP (from XLS-R CTC posteriors) as the primary continuous error signal, cross-checked against a phoneme confusion matrix for substitution typing, with edit-distance-derived insertion/deletion flags for cases where alignment itself fails (which GOP alone won't catch well). This hybrid is consistent with how recent MDD systems combine acoustic, phonetic, and linguistic cues rather than relying on a single score.

**GOP variant choice matters.** Use **logit-based GOP rather than the classical softmax-probability GOP**: computing GOP from raw pre-softmax logits (e.g., GOP_MaxLogit — the logit of the expected phone; GOP_Margin — expected-phone logit minus the highest competing logit) has been shown to correlate better with human pronunciation ratings than probability-based GOP on standard benchmarks (SpeechOcean762), because softmax saturates and compresses exactly the fine-grained differences a distortion detector needs. Use GOP_Margin for binary correct/mispronounced thresholding (better separation) and GOP_MaxLogit where you want a continuous severity-like score.

**Clinical validation precedent worth anchoring to**: a South Korean study fine-tuned wav2vec2-XLS-R-1B on just 93.6 minutes of disordered children's speech (73 target words, 95 children) and achieved ICC = 0.984 against SLP-rated percentage-of-consonants-correct on a standardized test (APAC), with a companion study reporting ~10% PER against human phonetic transcriptions on a 137-child sample. This is the strongest existing evidence that your Stage 2–3 pipeline can reach clinical-grade reliability with a *small* amount of labeled disordered-child speech — but note it followed an established hospital referral pipeline with children already clinically diagnosed; replicate the fine-tuning recipe, not the assumption that recruitment will be equally fast in a new setting.

For the **specific error subtypes** you listed (nasalization, aspiration, articulation errors — all clinically important in Urdu, which has phonemic aspiration contrasts, e.g. /p/ vs /pʰ/, and nasal vowels): these require **distinctive-feature-level modeling**, not just phone-identity comparison. Map each Urdu phone to its articulatory feature bundle (place, manner, voicing, aspiration, nasality) and compute GOP/confusion at the feature level as well as the phone level — this is exactly the approach in recent phonological-feature-aware GOP work (Parikh et al. 2024/2025, "Enhancing GOP with Phonological [features]"), which improves detection specifically for feature-level errors like devoicing or denasalization that phone-only comparison misses.

---

## 4. Speech Disorder Classification

The clinical categories you listed have real diagnostic overlap and disagreement even among human SLPs — recent work explicitly re-examines "ground truthing" for exactly this reason, noting the field's own major diagnostic frameworks split disorders into phonological delay, consistent/inconsistent phonological disorder, articulation disorder, and childhood apraxia of speech (CAS) as a distinct category, with dysarthria typically differentiated separately via motor/neurological signs. Build your classifier around **error-pattern signatures**, not audio alone:

**Feature inputs** (in order of clinical grounding):
- Phoneme-level error-type distribution (rates of substitution/deletion/insertion/distortion) from Stage 3
- Consistency of errors across repeated productions of the same target (a core CAS marker — inconsistent phonological disorder is defined by *variable* error patterns on repeated attempts of the same word)
- Phonological process patterns (fronting, stopping, cluster reduction — rule-based over the confusion matrix) vs. idiosyncratic/non-rule-governed errors (more apraxia/dysarthria-like)
- Prosodic/acoustic features (rate, pause patterns, voice quality, articulation precision) — these matter specifically for **dysarthria**, which is a motor execution disorder rather than a phonological/linguistic one; acoustic-feature-based dysarthria classifiers (wavelet-scalogram + CNN, ~98% reported accuracy in controlled settings) show this signal is strong when included
- Raw self-supervised embeddings (pooled XLS-R representations) as a supplementary channel, since self-supervised representations have shown value for pathological-speech detection and severity classification (e.g., wav2vec-based dysarthria detection/severity work) beyond hand-crafted features alone

**Model recommendations**:
- **Multi-task hierarchical classifier**: first split typical vs. disordered, then (for disordered) split motor-based (dysarthria/CAS) vs. linguistic-based (phonological/articulation/delay) using the consistency and prosody features, then fine-grained category within each branch. This mirrors clinical differential-diagnosis logic and lets you route dysarthria detection (needs prosody/acoustic features) differently from phonological-pattern detection (needs error-consistency features) rather than forcing one representation to do both jobs.
- **BiLSTM or temporal CNN** over the per-phone error/GOP sequence — good, lightweight choice for capturing sequential/positional error patterns (e.g., errors concentrated word-finally vs. word-initially) at low compute cost, appropriate given your eventual embedded-device target.
- **Transformer classifier** over the same sequence if you have enough labeled examples per category (likely only after Phase 2+ data collection, see Section 7) — expect this to outperform BiLSTM once you have on the order of hundreds of labeled Urdu children per category, not before.
- **Graph Neural Networks**: relevant here specifically because articulatory-trait relationships (place/manner/voicing graphs between phones) can be modeled explicitly — this is precisely what graph-based MDD modeling has shown improves diagnosis by encoding phonetic/articulatory structure as a graph rather than a flat feature vector (Yan et al. 2023, graph-based articulation-trait MDD). Worth prioritizing over a plain transformer if your labeled data is small, since the graph structure injects linguistic prior knowledge the model would otherwise have to learn from data you don't have.

**Speaker overfitting is a real, documented failure mode to design around from day one.** A wav2vec2-based dysarthria-severity classifier that fine-tuned naively overfit to individual speakers' voice characteristics rather than learning disorder-relevant features; the fix (Speaker-Agnostic Latent Regularization, SALR) added a multi-task triplet-margin contrastive loss that pulls same-severity embeddings together and pushes different-speaker embeddings apart regardless of severity, lifting accuracy from a prior SVM benchmark to 70.5% on a 15-speaker dysarthria set. With an Urdu cohort likely to start in the same small-N, high-per-speaker-variance regime, build this in from the start rather than discovering the overfitting problem after the fact: train the disorder classifier with a **primary cross-entropy loss on disorder/severity plus an auxiliary speaker-contrastive (or gradient-reversal speaker-adversarial) loss**, alongside the age-prediction auxiliary task already recommended above. Note SALR's validation is on adult English dysarthria (UA-Speech), not children or Urdu — treat it as a technique to adopt, not a result to expect to reproduce.

Given the very small expected N for a first Urdu cohort, **do not build separate classifiers per disorder category from scratch**. Start with (a) typical vs. disordered binary detection (easiest, most transferable, most clinically useful as a first-pass screener) and (b) rule-based phonological-process flags from the confusion matrix (interpretable, requires no labeled disorder data at all, only correct/expected phoneme pairs), and treat full 5-way disorder classification as a Phase 3 goal once sufficient labeled Urdu clinical data exists.

---

## 5. English → Urdu Transfer Learning

- **Multilingual pretraining** (XLS-R/MMS) > **English-only** models (Wav2Vec2-base, HuBERT-English, Whisper-English-only): confirmed repeatedly — multilingual pretraining outperforms monolingual pretraining for downstream cross-lingual fine-tuning, and specifically for phonetic-similarity-encoding representations useful in low-resource fine-tuning.
- **Cross-lingual transfer** works best when (a) the pretraining set included the target language (Urdu is in XLS-R's 128 and MMS's 1000+ language pretraining sets) and (b) related, higher-resource languages are also present (Hindi is comparatively higher-resource within the same phonetic cluster).
- **Domain adaptation**: your domain gap is not just language but also *speaker population* — children, and specifically children with speech disorders, differ acoustically from adult read-speech (higher pitch, more variable rate, atypical articulation). Plan a two-step domain adaptation: general-Urdu fine-tune → child-Urdu (typically developing) fine-tune → disordered-Urdu-child fine-tune, each step using progressively smaller but more targeted data, consistent with how continual pretraining / staged fine-tuning is used elsewhere in low-resource ASR transfer chains.
- **Continual pretraining**: if compute allows, a further self-supervised (masked/contrastive) continual-pretraining pass on unlabeled Urdu child speech (even without transcripts) before CTC fine-tuning — cheap to collect (no clinician annotation needed) and directly improves the encoder's fit to child-voice acoustics before you spend scarce annotated data on fine-tuning.
- **Phoneme inventory adaptation**: don't reuse XLS-R's default multilingual phoneme/character output vocabulary as-is — replace the final CTC layer's vocabulary with the Urdu-specific phoneme set (Section 2/6) and reinitialize just that layer, keeping the pretrained encoder body.
- **XLS-R/MMS vs. English-only**: for phoneme-level tasks specifically, the zero-shot cross-lingual phoneme recognition literature (Xu, Baevski & Auli) built directly on XLS-R and demonstrated phone-level transfer without needing target-language fine-tuning data at all in some settings — this is a meaningful capability if labeled Urdu phoneme data is initially near-zero, letting you bootstrap error detection before large-scale annotation is complete.

---

## 6. Fine-Tuning Hindi Models for Urdu

This is genuinely one of your strongest levers, more so than generic multilingual XLS-R fine-tuning, because Hindi and Urdu are the same spoken language (Hindustani) with different scripts and different formal/loanword vocabulary — phonetically and phonologically they are extremely close.

- **Available Hindi pretrained models**: **IndicWav2Vec** (AI4Bharat), pretrained on ~17,000 hours across 40 Indic languages including Hindi, with published Hindi fine-tuned checkpoints; **CLSRIL-23**, pretrained on ~10,000 hours across 23 Indic languages, explicitly demonstrating that Hindi, Sanskrit, Urdu and Punjabi cluster together in the learned phonetic representation space, with multilingual pretraining reducing Hindi WER by 5% and CER by 9.5% relative to monolingual.
- **Multilingual Indic models**: IndicWav2Vec's own ablations show multilingual pretraining outperforming monolingual specifically because it reduces WER/CER further for lower-resource languages in the same family, and IndicSUPERB — the standard Indic speech benchmark suite — explicitly **includes Urdu** alongside Hindi, Punjabi, Bengali, etc., meaning some Urdu-labeled benchmark data already exists in this ecosystem and is a good place to start for evaluation, not just Hindi transfer.
- **Vocabulary/tokenizer adaptation**: Hindi models use Devanagari-script tokenizers/CTC vocabularies; Urdu uses a Perso-Arabic script (Nastaliq). At the **word/character level this is a mismatch you must not transfer directly** — but at the **phoneme level it's largely irrelevant**, since phoneme labels are script-independent. This is the core argument for the phoneme-first architecture in Section 1: it lets you inherit Hindi's acoustic-phonetic knowledge while discarding its (incompatible) orthographic output layer entirely.
- **Phoneme mapping**: build an explicit Hindi-phone → Urdu-phone mapping table (they are near-identical for the shared Hindustani core, with Urdu adding a handful of Perso-Arabic-derived phonemes/allophones like /q/, /x/, /ɣ/, /z/ series not native to Hindi, and Urdu's phonemic aspiration/nasalization contrasts needing careful alignment). Use this mapping to relabel or bootstrap a Hindi phone recognizer's output as weak/pseudo-labels for initial Urdu data.
- **Expected performance gains**: based on the CLSRIL-23 and IndicWav2Vec findings, expect fine-tuning a Hindi-pretrained (or Indic-multilingual-pretrained) encoder on even modest amounts of Urdu data to outperform fine-tuning generic XLS-R directly, due to the tighter phonetic-cluster match — though note recent large-scale dialect-transfer evaluation found IndicWav2Vec-Hindi still had a best-case WER around 50% even on held-out Hindi dialect speech, a useful reality check that transfer helps but does not solve low-resource ASR outright, and real Urdu fine-tuning data remains necessary.
- **Limitations**: Hindi models won't natively cover Perso-Arabic loan-phonemes correctly without Urdu-specific fine-tuning data including words that exercise them; over-relying on Hindi transfer risks systematically under-detecting errors precisely in the phonemes that differentiate Urdu from Hindi.

**Recommended approach**: pretrain/initialize from an Indic-multilingual encoder (IndicWav2Vec or CLSRIL-23-style, or XLS-R as a fallback if those aren't accessible), fine-tune the CTC head on the Urdu phoneme inventory using available Urdu ASR data (Section 7), using the Hindi-Urdu phoneme mapping to seed/pretrain the new phoneme classifier layer before Urdu-specific data fine-tuning, rather than random layer initialization.

---

## 7. Datasets

| Dataset | Language | Speakers / Hours | Age | Phoneme annotation | Disorder annotation | License | Strengths | Weaknesses |
|---|---|---|---|---|---|---|---|---|
| **UltraSuite** (UXTD/UXSSD/UPX/UX2020) | English | 86–120+ children across sub-corpora, ~18.7h core | 5;8–13;4 | Yes (phone/word, Praat TextGrid + HTK lab) | Yes (SSD vs. typically developing, some diagnostic labels) | Academic/research (UltraSuite site) | Only public child-SSD corpus with fine phone-level alignment; excellent methodology template; ultrasound tongue imaging as bonus articulatory ground truth | **English only**; small; not usable as Urdu training data |
| **Mozilla Common Voice — Urdu** | Urdu | Community-crowdsourced, growing over versions (UrduSpeakXLSR work used CV v11) | Adult-skewed, read speech | No native phoneme labels (word transcripts only; phonemes derivable via G2P) | No | CC0 | Largest open Urdu speech resource; free, permissively licensed; multiple published wav2vec2/XLS-R baselines to build on | Adult, read-speech, no children, no disorder labels, variable audio quality/noise |
| **IndicSUPERB** | 12 Indic languages incl. **Urdu** | Benchmark-scale per language | Adult | Task-dependent (ASR/phoneme benchmark tasks) | No | Research license (AI4Bharat) | Standardized Indic benchmark including Urdu; useful for evaluating transfer quality against a known baseline | Adult, general-domain, not clinical/child |
| **OpenSLR Urdu resources** (e.g., SLR119 and related South Asian language corpora) | Urdu (varies by SLR id) | Varies | Mostly adult | Varies | No | Open (per-corpus, mostly CC) | Free, easy to script into pipelines | Fragmented, quality/size varies a lot by corpus, no children |
| **Google FLEURS** | 100+ languages incl. Urdu | ~10h read speech per language | Adult | No native phoneme labels | No | CC-BY | Clean, standardized, parallel across languages (good cross-lingual eval) | Very small per language, read speech, adult, no disorder data |
| **MMS unlabeled/labeled data (Meta)** | 1000+ languages incl. Urdu | Pretraining-scale (unlabeled) | Adult-skewed | No | No | Research/CC (per Meta's release) | Best raw-audio coverage for further self-supervised continual pretraining on Urdu | Not clinical, not child, largely religious-text-read speech (New Testament-style recordings) which biases domain/style |
| **CLSRIL-23 / IndicWav2Vec pretraining corpora** (incl. Hindi from MUCS, OpenSLR, YouTube/News-on-air) | 23–40 Indic langs, incl. Hindi (Urdu's closest relative) | ~10,000h (CLSRIL-23), ~17,000h (IndicWav2Vec) | Adult | No | No | Research (AI4Bharat) | Best available proxy for Urdu acoustic-phonetic pretraining via Hindi | Not Urdu itself; must be used via transfer, not direct fine-tuning |
| **TORGO / other dysarthria corpora (adult)** | English | Small, clinical | Adult | Some | Yes (dysarthria) | Research/academic | Useful for pretraining/validating the *disorder-classification stage's* architecture (feature engineering, evaluation protocol) even though not Urdu or child | Adult, English, small |
| **CHILDES / IPA-CHILDES** | Many, not Urdu-focused | Corpus-dependent | Child | Yes (via G2P+/Phoible for IPA-CHILDES) | No | Open (CHILDES license terms) | Good template for child-speech phonemic transcription pipelines and phonological-process analysis methodology | No Urdu subset of note; no disorder labels |
| **Urdu speech disorder / child speech corpora** | Urdu | **None found publicly as of this writing** | — | — | — | — | — | **This is the actual gap you must fill — see Section 7a below** |

### 7a. The data-collection plan you actually need

Given the gap above, structure data acquisition in phases:
1. **Phase 0 (exists today)**: Common Voice Urdu + OpenSLR Urdu + FLEURS Urdu + IndicSUPERB Urdu → used to build and validate the Urdu ASR/phoneme-recognition backbone (adult, but establishes the phoneme-recognition capability).
2. **Phase 1 (low-cost, achievable)**: record **typically developing Urdu-speaking children** reading/repeating a fixed, phonemically-balanced word/sentence list (design this list explicitly to cover every Urdu phoneme, especially aspirated/nasal/retroflex contrasts, multiple times each — directly modeled on how UltraSuite's own elicitation prompts and CAPE-V-style standardized elicitation work) — this alone lets you validate the phoneme-recognition pipeline on genuine Urdu child voices and establish a "typical error" baseline, with no clinical/diagnostic burden.
3. **Phase 2 (requires SLP partnership)**: recruit Urdu-speaking children with clinician-confirmed SSD diagnoses (through speech therapy clinics/hospitals in Urdu-speaking regions) using the same elicitation protocol, with SLP-provided ground-truth phonetic transcription and disorder category for a genuinely clinically-validated dataset — this is the true bottleneck and should start in parallel with Phase 0/1 model development, not after.
4. **Data-sharing note**: strongly consider designing this Phase-2 collection for eventual publication (with appropriate consent/ethics review) — an Urdu child-SSD corpus release would itself be a significant contribution, similar in spirit to how UltraSuite filled that role for English.

---

## 8. Data Augmentation

| Method | Effect | Recommended for children's speech? |
|---|---|---|
| **SpecAugment** (time/freq masking) | Regularizes against overfitting to specific frequency bands/time spans | Yes — cheap, standard, low risk of distorting clinically meaningful cues |
| **Speed perturbation (0.9x–1.1x)** | Simulates rate variability | Yes, but keep the range **narrower** than typical adult-ASR recipes (e.g., ±10% not ±20%) — child speech already has naturally high rate variability and disordered speech specifically may have atypical rate (relevant to dysarthria); over-perturbing risks manufacturing "fake" rate-based error signals |
| **Pitch shifting** | Simulates F0 variability | Use cautiously and in a **narrow** range — children's F0 range is already high and variable; large pitch shifts can push samples outside plausible child-voice range and distort formant relationships that matter for vowel/distortion detection |
| **Noise injection** | Robustness to real-world recording conditions | Yes — important for a portable device used in varied home/clinic acoustic environments |
| **Room impulse response (RIR) convolution** | Robustness to reverberation | Yes — same rationale, especially for non-clinic (home) deployment |
| **Vocal Tract Length Perturbation (VTLP)** | Simulates different vocal tract lengths | **Particularly valuable here** — it's specifically designed to simulate the shorter vocal tracts / different formant spacing of children vs. the adult speakers most pretraining data comes from, directly addressing the adult-to-child domain gap |
| **Synthetic/TTS-generated Urdu data** | Expands labeled phoneme coverage cheaply | Useful for **balancing rare phonemes** in the expected-phoneme distribution (Section 2 G2P output can drive targeted TTS generation, e.g. via a fine-tuned XTTS-v2 Urdu voice) — but do **not** use synthetic children's-voice TTS as disorder-classifier training data, since disordered speech patterns are not something Urdu child TTS voices exist to simulate; safe uses are limited to bootstrapping the phoneme-recognition stage's linguistic/phonemic coverage. Note: a public 4,000-hour multilingual synthetic corpus (IndicSynth) does include ~72 hours of XTTS-v2-generated Urdu speech, but it was built for **audio-deepfake-detection research**, not ASR augmentation — it's a useful engineering reference for how to fine-tune XTTS-v2 on Urdu, not a ready-made ASR training addition, and shouldn't be cited as validated ASR-augmentation evidence. |
| **Phoneme balancing** | Ensures rare phones (many Urdu-specific ones) aren't underrepresented | Important given the modest expected dataset size — actively oversample utterances containing rare/aspirated/nasalized Urdu phonemes |
| **Curriculum learning** | Order training from easy→hard examples | Recommended for the staged transfer approach in Sections 5–6: Hindi-pretrained → clear Urdu speech → progressively more disordered/harder Urdu child speech |

**Bottom line for children's speech**: prioritize VTLP, modest speed/pitch perturbation, SpecAugment, and noise/RIR augmentation; be conservative with pitch/speed extremes and avoid synthetic disordered-speech generation for the classification stage.

---

## 9. Evaluation

**Phoneme recognition (Stage 2)**
- **PER (Phoneme Error Rate)** — primary metric, directly comparable to the UltraSuite English benchmark (PER 0.15) as your target reference point, adjusted for the added difficulty of Urdu + disordered speech
- CER/WER — secondary, if you also expose a word-level transcript
- Alignment accuracy (against manually-verified subset, as UltraSuite itself does with its manually-revised reference labels) — critical, since Stage 3/4 quality is bounded by alignment quality

**Speech-error detection (Stage 3)**
- Precision/recall/F1 **per error type** (substitution, deletion, insertion, distortion, nasalization, aspiration) — do not report a single pooled F1, since clinically some error types (e.g., missed CAS-relevant inconsistency) matter more than others and pooling hides that
- Confusion matrix, phone-by-phone — this doubles as a clinical/diagnostic artifact, not just an eval tool
- Correlation of GOP scores against SLP severity ratings on a validation subset (as done in the facial-palsy GOP validation study) — the most clinically meaningful validation you can run, since it directly tests whether your continuous error score tracks human clinical judgment

**Disorder classification (Stage 4)**
- Accuracy — report but don't lead with it, given expected class imbalance
- **Macro F1** — primary metric, since disorder categories will be imbalanced and macro F1 penalizes ignoring rare classes (e.g., CAS is rarer than general phonological delay)
- ROC-AUC per class (one-vs-rest)
- Sensitivity/specificity — especially important for a screening device, where you need to explicitly report the false-negative rate (missed disorders) separately from false-positive rate, since the clinical cost of each differs

**Cross-cutting**: report all of the above **separately for typically-developing vs. disordered children**, and **separately by disorder subtype**, not pooled — pooled metrics will look artificially strong (typical speech is easy) and hide the failure modes that matter most for a diagnostic device.

---

## 10. Deployment

- **Lightweight models**: target **XLS-R-300M or smaller** (not 1B/2B) for the deployed phoneme-recognition encoder; the disorder-classification head (BiLSTM/small transformer over phone-level features) is tiny by comparison and not the bottleneck. For a second-generation device, consider **knowledge distillation** down to a ~30–90M-parameter student (distilling from your fine-tuned 300M teacher) as a further step beyond quantization alone — expect a modest PER increase in exchange for a roughly 3–4x parameter reduction; validate this trade-off empirically before committing, since published child/disordered-speech distillation numbers specific to this domain don't yet exist and shouldn't be assumed from general-ASR distillation results.
- **Model compression**: prune the encoder (structured pruning of attention heads/conv channels) and **quantize to INT8** post-training. Published edge-ASR evaluations show quantized wav2vec2 models achieve real-time-factor (RTF) < 1.0 on Raspberry Pi 4 CPU with only modest WER degradation, and quantized Whisper releases achieve >3.7x compression with marginal accuracy loss and up to 15% latency reduction on Raspberry Pi 5 — directly relevant precedents for your target hardware class.
- **ONNX**: export the fine-tuned encoder + CTC head to ONNX for portable, framework-independent inference; combine with ONNX Runtime's quantization tooling.
- **TensorRT**: if targeting NVIDIA Jetson specifically, TensorRT gives the larger latency win — published Jetson Nano evaluations show **3–5x latency improvement over Raspberry Pi CPU inference** for transformer-based ASR, with ~1–2s load time and ~300MB memory footprint achievable for optimized transformer speech models.
- **Edge inference — hardware recommendation**: **NVIDIA Jetson Orin Nano** (or Jetson Nano as a lower-cost/lower-power option) over Raspberry Pi alone, if GPU-accelerated inference is affordable for the device's cost target; Raspberry Pi 4/5 CPU-only inference is viable as a lower-cost fallback given the RTF<1.0 results above, but expect to skip on-device forced-alignment/GOP computation complexity in favor of the simplest possible Stage 2–3 pipeline at the edge.
- **Compute budget estimate**: a quantized XLS-R-300M-class encoder plus lightweight CTC/GOP/classifier stages should fit comfortably within a ~1–2GB RAM budget and achieve real-time or faster processing on Jetson-class hardware, and near-real-time (RTF close to 1) on Raspberry Pi 4/5 CPU — consistent with the cited edge-ASR benchmarks, though you should validate this directly once your fine-tuned model exists, since exact figures depend on final model size and the added Stage 3/4 compute.
- **Practical recommendation**: for a first-generation device, consider a **hybrid architecture** — run Stage 1–2 (phoneme recognition) on-device for privacy/latency, and optionally offload Stage 3–4 (GOP scoring, disorder classification, and any LLM-based report generation) to a lightweight cloud/companion-app service if connectivity is available, falling back to fully on-device operation when offline. This avoids forcing the heaviest/least-validated stages (disorder classification, which needs the most iteration as your dataset grows) into a fixed embedded footprint too early.

---

## 11. Recommended End-to-End Pipeline (Summary)

**Architecture**: Indic-multilingual-pretrained encoder (IndicWav2Vec/CLSRIL-23, fallback XLS-R-300M) → Urdu phoneme-level CTC head (Phoible-aligned inventory, PronouncUR-derived lexicon/G2P) → forced alignment → GOP + feature-level (place/manner/voicing/aspiration/nasality) + confusion-matrix error detection → hierarchical BiLSTM/graph-based classifier for disorder categorization.

**Training stages**:
1. Self-supervised continual pretraining on unlabeled Urdu audio (Common Voice + OpenSLR + MMS-derived Urdu audio), starting from an Indic-multilingual checkpoint.
2. CTC fine-tuning on Urdu phoneme recognition using Common Voice/OpenSLR/FLEURS Urdu (via G2P-derived phoneme labels) plus your Phase-1 typically-developing Urdu child recordings.
3. GOP/error-detection calibration using forced-alignment + confusion-matrix analysis, validated against a manually phonetically-transcribed subset.
4. Disorder classifier training only once Phase-2 clinically-labeled data exists, starting with binary typical-vs-disordered screening before attempting full 5-way classification.

**Datasets**: Common Voice Urdu + OpenSLR + FLEURS + IndicSUPERB (Phase 0); newly collected typically-developing Urdu child speech on a phonemically-balanced elicitation list (Phase 1); clinician-partnered Urdu child SSD corpus (Phase 2, the critical long-lead item — start recruitment now, in parallel with Phase 0/1 engineering).

**Preprocessing/augmentation**: VAD + denoising front end; VTLP + modest speed/pitch perturbation + SpecAugment + noise/RIR injection; phoneme-balanced sampling; TTS-augmented phoneme coverage (recognition stage only, not classification stage).

**Evaluation**: PER/alignment-accuracy for Stage 2; per-error-type P/R/F1 + confusion matrix + GOP-vs-clinician-rating correlation for Stage 3; macro-F1 + sensitivity/specificity, reported per-subtype and not pooled, for Stage 4.

**Deployment**: INT8-quantized, pruned XLS-R-300M-class encoder exported to ONNX/TensorRT, targeting Jetson Orin Nano (preferred) or Raspberry Pi 4/5 (budget fallback), with on-device phoneme recognition and either on-device or hybrid-offload disorder classification.

**Why this is likely to work best for Urdu-speaking children with SSDs specifically**: it explicitly exploits the one strong transfer-learning lever that exists (Hindi/Indic phonetic proximity to Urdu, empirically confirmed by codebook-clustering studies), decomposes an otherwise data-starved end-to-end problem into stages that can each be bootstrapped from *some* existing resource (adult Urdu ASR data → phoneme recognition; UltraSuite methodology → alignment/error-detection design; English/Chinese/Korean SSD-classification literature → classifier architecture choices), and is honest about the one piece nothing can substitute for — a genuine, clinician-annotated Urdu child speech-disorder corpus — treating its collection as parallel critical-path work rather than an afterthought.

---

## Key references (non-exhaustive, 2018–2026)

- Eshky et al. (2018/2019), *UltraSuite: A Repository of Ultrasound and Acoustic Data from Child Speech Therapy Sessions*, INTERSPEECH.
- Conneau et al. (2020) / Babu et al. (2021), *XLSR* / *XLS-R: Self-supervised cross-lingual speech representation learning at scale*, INTERSPEECH 2022.
- Xu, Baevski & Auli (2022), *Simple and effective zero-shot cross-lingual phoneme recognition*, INTERSPEECH.
- Pratap et al. (2023), *Scaling speech technology to 1,000+ languages* (MMS), arXiv:2305.13516.
- Gupta et al. (2021)/AI4Bharat, *IndicWav2Vec: Robust ASR for Indic Languages*.
- Javed et al. (2021), *CLSRIL-23: Cross Lingual Speech Representations for Indic Languages*, arXiv:2107.07402.
- Sarfraz et al. (2018), *PronouncUR: An Urdu Pronunciation Lexicon Generator*, LREC.
- Peng, Fu, Lin, Ke & Zhang (2021), *A Study on Fine-Tuning wav2vec2.0 Model for the Task of Mispronunciation Detection and Diagnosis*, INTERSPEECH.
- Wu, Li, Leung & Meng (2021), *Transformer Based End-to-End Mispronunciation Detection and Diagnosis*, INTERSPEECH.
- Yan, Wang, Wang & Chen (2023), *Effective graph-based modeling of articulation traits for mispronunciation detection and diagnosis*, ICASSP.
- Parikh, Tejedor-Garcia, Cucchiarini & Strik (2024/2025), *Enhancing GOP in CTC-Based Mispronunciation Detection with Phonological Features*, Language Learning & Technology.
- Sung, So, Yoon & Ha (2024), *Automatic detection of speech sound disorder in children using ASR and audio classification*, Phonetics and Speech Sciences.
- Wang et al. (2024), *Deep-Learning-Based Automated Classification of Chinese Speech Sound Disorders*, Chinese Medicine.
- Cleland et al. (2025), *Reevaluating the classification of pediatric speech sound disorders: a ground truthing perspective*, Frontiers in Human Neuroscience.
- Al Ani, Cleland & Zoha (2025), *Deep learning in ultrasound tongue imaging: a systematic review toward automated detection of speech sound disorders*, Frontiers in AI.
- Goriely & Buttery (2025), *IPA CHILDES & G2P+: Feature-Rich Resources for Cross-Lingual Phonology and Phonemic Language Modeling*, arXiv:2504.03036.
- Edge-inference benchmarks: *Performance Evaluation of Offline Speech Recognition on Edge Devices* (Electronics/MDPI 2021); *Wav2Vec2.0 on the Edge: Performance Evaluation* (arXiv:2202.05993); *Speech recognition in edge environments: model compression* (Language Resources and Evaluation, 2026).

- Ahn et al. / follow-up (2025), *Usefulness of Automatic Speech Recognition Assessment of Children With Speech Sound Disorders: Validation Study*, Journal of Medical Internet Research 27:e60520 — the ICC=0.984 Korean XLS-R clinical validation result.
- Stumpf, Kadirvelu, Waibel & Faisal (2024), *Speaker-Independent Dysarthria Severity Classification using Self-Supervised Transformers and Multi-Task Learning* (SALR), arXiv:2403.00854 / PLOS Digital Health.
- Sharma, Ekbote & Gupta (2025), *IndicSynth: A Large-Scale Multilingual Synthetic Speech Dataset for Low-Resource Indian Languages*, ACL 2025 — cited here specifically as an XTTS-v2 Urdu fine-tuning reference, not as ASR-augmentation evidence (its actual purpose is audio deepfake detection).

*Note: some 2025–2026-dated sources above reflect this report's search date and should be re-verified for currency given the fast-moving nature of this field.*

---

## Appendix: Verification notes

This report was cross-checked against a second independently-produced pipeline covering the same brief. Two of its claims materially improved this document and are incorporated above: the Korean XLS-R clinical-validation study (ICC=0.984 from 93.6 minutes of fine-tuning data) and the SALR speaker-agnostic multi-task technique for small-N disorder classifiers — both verified against their primary sources before inclusion. One claim from that pipeline was not carried over: it cited IndicSynth as evidence that synthetic Urdu data "can augment real data for low-resource [ASR] scenarios," but IndicSynth's actual stated purpose is audio-deepfake-detection research, not ASR training augmentation — the dataset and hour-count are real, the framing of what it demonstrates was not, so it's cited above only as an XTTS-v2 fine-tuning reference. A separate claim (Kazakh cross-lingual transfer via meta-learning, cited as support for Hindi→Urdu transfer) was omitted here as a non-sequitur — Kazakh is Turkic and phonologically unrelated to the Hindi-Urdu cluster, so it doesn't strengthen that argument regardless of whether the underlying number is accurate. Treat any specific benchmark number in this space — including the ones retained here — as worth re-verifying against the primary paper before it goes into a grant application or manuscript.

---

## Appendix: Related Projects & Code for Further Reading

A curated set of GitHub repositories and papers relevant to different components of this pipeline, found via direct research rather than assumed from memory. Descriptions below are paraphrased summaries of each project's own stated purpose, not quotations.

### Mispronunciation Detection / GOP (relevant to Section 3, and the GOP pipeline in Doc C Section 4)

- **crazycloud/mispronunciation-detection-diagnosis-wav2vec2-and-llm** (github.com/crazycloud/mispronunciation-detection-diagnosis-wav2vec2-and-llm) — an architecture close to this project's own: fine-tuned wav2vec2 for phoneme recognition, eSpeak for generating the reference phoneme sequence, alignment between predicted and reference phonemes (via Needleman-Wunsch rather than CTC Viterbi — a different alignment algorithm worth comparing), followed by an LLM layer that turns raw phoneme mismatches into human-readable feedback. That last piece doesn't exist in this pipeline yet and could be a useful future addition once GOP flagging is validated against real recordings.
- **vocaliodmiku/wav2vec2mdd** (github.com/vocaliodmiku/wav2vec2mdd) — end-to-end MDD fine-tuning on the L2-ARCTIC dataset, built on fairseq. Its evaluation methodology references cageyoko/CTC-Attention-Mispronunciation, a commonly-cited reference point in the MDD literature for phoneme-level error-detection scoring.
- **Evanchan1923/MDD_SpeechAttribute** (github.com/Evanchan1923/MDD_SpeechAttribute) — a Mandarin MDD system doing feature-level (not just phone-level) diagnosis, combining place/manner-of-articulation attributes with tonal distinctions to give interpretable feedback (e.g. "missing aspiration") rather than just a wrong-phone flag. Conceptually close to the feature-level GOP extension already flagged in Section 3 for nasalization/aspiration-specific Urdu error detection — worth reading their attribute-confusion methodology directly.

### Forced Alignment (relevant to Doc C Section 4's Viterbi implementation)

- **PyTorch's official CTC forced alignment tutorial** (docs.pytorch.org/audio/stable/tutorials/ctc_forced_alignment_api_tutorial.html) — documents a real CTC failure mode called "peaky behavior," where models trained with CTC tend to spike briefly at a label's onset rather than sustaining probability mass across the full label duration. This can distort frame-count-based GOP averaging if unaccounted for. Also documents `torchaudio.functional.forced_align()`, a production-grade C++/CUDA implementation worth benchmarking against the pure-Python Viterbi implementation already built for this project, for speed once processing real volumes of child recordings.
- **MahmoudAshraf/ctc-forced-aligner** (github.com/MahmoudAshraf97/ctc-forced-aligner) — a memory-efficient reimplementation of forced alignment built on Meta's MMS-300M checkpoint, explicitly designed to use less memory than the standard torchaudio API. Worth evaluating as a drop-in replacement given this project's 6GB VRAM constraint, if alignment at scale ever hits memory pressure.

### Indic/Hindi-Urdu Transfer (relevant to the Backbone-v1 decision, Doc C Section 5)

- **AI4Bharat/IndicWav2Vec** (github.com/AI4Bharat/IndicWav2Vec) — the training repo behind the model this project fine-tuned as Backbone-v1. Worth reading its fairseq-based fine-tuning configs and data-prep scripts (even though the HuggingFace-converted checkpoint was used here) for hyperparameter reference on future fine-tuning runs, e.g. on child speech data.
- **AI4Bharat/IndicSUPERB** (github.com/AI4Bharat/indicSUPERB) — the benchmark suite behind the Kathbath dataset already used in this project. Its evaluation-task structure is worth reviewing for ideas on building a more formal benchmark protocol for the Urdu phoneme recognizer going forward.

### Child Speech Disorder Detection (the end goal — relevant to Section 4)

- **toopster/dsc-capstone-project** (github.com/toopster/dsc-capstone-project) — a smaller CNN-based classifier for atypical child speech, worth reading specifically for its honest documentation of overfitting problems and its explicit acknowledgment that a model trained only on typical speech doesn't generalize to disordered speech without disordered training examples — independent real-world confirmation of exactly the Phase 2/3 data bottleneck already identified as this project's critical path (Doc D).
- *Automatic Detection of Speech Sound Disorder in Child Speech Using Posterior-based Speaker Representations* (arXiv:2203.15405) — takes a contrasting architectural approach: instead of scoring individual phonemes, it builds one subject-level representation by concatenating a child's full test-word set and classifies the whole thing at once. Worth reading as a complementary design philosophy to this project's phone-by-phone GOP approach — potentially useful as an additional holistic severity signal alongside the per-phone error map, not a replacement for it.
- The Frontiers systematic review on deep learning for ultrasound tongue imaging in SSD detection (already cited above) is worth revisiting directly at this stage of the project — its "developmental pipeline" framing (preprocessing → phoneme-level classification on typically-developing speakers → preliminary disorder classification) maps closely onto this project's own phased roadmap (Doc D), and its stated field-wide gap (small disorder-focused datasets, lack of integrated end-to-end systems) is effectively independent confirmation that this project's structure and current bottleneck reflect the actual state of the field, not a project-specific shortcoming.
