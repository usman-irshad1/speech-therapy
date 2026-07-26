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

## 2. Audio → Phoneme Pipeline

1. **Feature extraction**: raw waveform (16kHz mono) directly into the self-supervised encoder — no hand-crafted MFCCs needed for the backbone; log-Mel/MFCC can still be computed as auxiliary features for the disorder classifier (Section 4) since prosodic/spectral cues matter for dysarthria specifically.
2. **Self-supervised encoder**: **XLS-R (300M as the practical default, 1B if compute allows)**. Rationale: it was pretrained on Urdu and on Hindi/Punjabi/Sanskrit, which cluster with Urdu in learned phonetic subspace — confirmed by CLSRIL-23's codebook-clustering analysis on Indic languages, which found Hindi, Sanskrit, Urdu and Punjabi group into a single cluster, and IndicWav2Vec analysis showing the same Hindi–Urdu–Punjabi codebook overlap. This cross-lingual phonetic proximity is the single most important transfer-learning lever available to you (expanded in Section 5–6).
3. **Phoneme recognition head**: replace the word/subword CTC output with a **phone-level CTC head** over the Urdu phoneme inventory (see below), rather than character/word output. Zero-shot cross-lingual phoneme recognition (Xu, Baevski & Auli, 2022, built on wav2vec2/XLS-R) is directly relevant: it shows phoneme-level CTC heads transfer across languages far better than word-level heads, because phones are more universal units than orthography.
4. **Forced alignment**: use the CTC posteriors (or a dedicated aligner such as Montreal Forced Aligner / Kaldi-based tools, or the WFST-topology approaches used in recent GOP work) to time-align the audio to the *expected* phoneme sequence derived from the prompt text. UltraSuite's own alignment pipeline (also wav2vec2-based, PER 0.15) is a good template even though it's English.
5. **IPA vs. language-specific inventory**: use a **Phoible-aligned Urdu phone set** (via a tool like G2P+/Phoible folding, as used in IPA-CHILDES) rather than an ad hoc inventory. This keeps you compatible with cross-lingual tools and with the Hindi/Indic phoneme mapping in Section 6. For the practical G2P step, **PronouncUR** (Sarfraz et al., LREC 2018) is the most directly relevant existing resource: an Urdu pronunciation-lexicon generator using CISAMPA phonetic notation over the Urdu script's 37 basic + 4 secondary letters and diacritics — this is your starting point for expected-phoneme-sequence generation, adapted/re-mapped to IPA.
6. **Confidence scores**: retain full CTC posterior distributions (not just argmax) per frame — these feed GOP scoring directly and also let you flag low-confidence segments for human SLP review rather than silently misclassifying them.
7. **Sequence decoding**: greedy CTC decoding is sufficient for phoneme-level output (unlike word-level ASR, an n-gram/KenLM phoneme language model can *hurt* here, since it biases the model toward "expected" phonemes and can mask the very substitution/distortion errors you're trying to detect — use LM-free decoding for error detection, and only add an LM if you also need a fluent word-level transcript for context).

**Whisper as ASR alternative**: not recommended as the phoneme backbone — its text-decoder architecture with implicit LM biasing is precisely the "auto-correct" failure mode that will hide disordered pronunciation, which several MDD papers explicitly flag as a risk with strong internal LMs.

### 2a. Canonical Urdu-IPA phoneme inventory (verified)

Consolidated from PronouncUR's CISAMPA lexicon (Sarfraz et al. 2018, Raza et al. 2010), the CLE reference inventory (Saleem et al. 2002), and Hussain's (2004) phonology description — cross-checked against multiple independent linguistic sources, with two corrections to a commonly-circulated version of this table flagged below.

| Category | IPA Symbol | Notes |
|---|---|---|
| Plosives | /p, b, t, d, ʈ, ɖ, k, g, q/ | Dental/retroflex contrast; uvular /q/ (Perso-Arabic loan) |
| Aspirated | /pʰ, bʰ, tʰ, dʰ, ʈʰ, ɖʰ, kʰ, gʰ/ | The voiceless/voiced × unaspirated/aspirated four-way contrast is a defining Indo-Aryan feature |
| Affricates | /tʃ, dʒ, tʃʰ, dʒʰ/ | Palatal series (phonetically affricates despite the "palatal stop" label in some older CLE literature) |
| Fricatives | /f, s, z, ʃ, x, ɣ, h/, marginally /ʒ/ | /x, ɣ, q/ are Perso-Arabic loans with dedicated Hindi nukta letters (ख़ ग़ क़); **/ʒ/ is marginal** — present orthographically (ژ) in rare literary Persian loans, absent from at least one SLP-oriented Urdu phonology reference's core inventory, and not reliably distinguished from /z/ or /dʒ/ by many speakers. Confirm with a linguist/SLP whether to include it before freezing your CTC vocabulary, given how little training signal it will have |
| Nasals | /m, n, ŋ/ | **Correction**: the retroflex nasal /ɳ/, sometimes listed in circulating Urdu phoneme tables, is not established as phonemic in Urdu — a CLE reference lists only /m, n, ŋ/, and a direct comparative statement in the ASR literature notes the retroflex-nasal contrast is present in Pashto but "absent from Arabic, Dari, and Urdu." Treat /ɳ/ as an allophone of /n/ before retroflex consonants, not an independent CTC class |
| Liquids/Glides | /l, r, ɽ, j, w/ (possibly /ɽʰ/) | Retroflex flap /ɽ/ is well-attested (Hindi ड़ / Urdu ڑ); at least one source describes Urdu's retroflex liquid as having both unaspirated and aspirated members — verify /ɽʰ/'s status against Hussain (2004) directly before deciding whether to include it as a separate class |
| Vowels | /i, e, ɛ, ɑ, ə, ɪ, ʊ, u, o, ɔ/ + nasalized set (/ĩ, ẽ, ɑ̃, ɪ̃, ʊ̃, ũ, õ, ɔ̃/) | Oral/nasal contrast is phonemic in Urdu, not merely coarticulatory — this is why nasalization needs its own feature-level GOP dimension (Section 3), not just phone-level treatment |

**Target count**: roughly 34–37 consonants + 10 oral vowels + a nasalized-vowel set, landing in the same ~38–44 phoneme range originally targeted, but with a different composition than a table that includes /ɳ/ and omits /ŋ/. Do a final reconciliation against Hussain (2004) and Saleem et al. (2002) directly — these are PronouncUR's own primary sources — before this inventory becomes your fixed CTC output vocabulary, since an error copied in at this stage propagates through every downstream stage (G2P, forced alignment, GOP, confusion matrices).

### 2b. Hindi-to-Urdu phoneme mapping (verified, with one mechanism correction)

| Urdu phoneme | Typical Hindi-model realization | Status | Why |
|---|---|---|---|
| /q/ | → /k/ | Loan, nukta-collapse | क़ (q) has a dedicated Hindi nukta letter; casual/nukta-dropped Hindi collapses it to क /k/ |
| /x/ | → /kʰ/ | Loan, nukta-collapse | ख़ (x) has a dedicated nukta letter; collapses to ख /kʰ/ |
| /ɣ/ | → /g/ | Loan, nukta-collapse | ग़ (ɣ) has a dedicated nukta letter; collapses to ग /g/ |
| /z/ | → /z/ (usually preserved) | Loan, largely integrated | ज़ (z) is a nukta letter but is common enough in everyday Hindi (loanwords like ज़रा, इज़्ज़त) that it's typically well-represented in Hindi ASR training data already — lower risk than q/x/ɣ |
| /ʒ/ | → variable (/z/, /ʃ/, or /dʒ/ depending on model) | **Different mechanism — no Hindi nukta letter exists for this sound at all** | This is *not* a nukta-dropping case like the four above (there's no dot to drop); a Hindi-pretrained model has essentially zero training exposure to this phone, which is a harder problem than nukta-collapse, not an equivalent instance of it |
| /ʈ, ɖ, ʈʰ, ɖʰ/ | 1:1 shared | Native | Retroflex series is native to both Hindi and Urdu (pre-dating the Perso-Arabic/Sanskrit split) |
| /ɳ/ | N/A | **Not applicable** — see 2a correction; don't build a mapping row for a phone that isn't established as phonemic in Urdu to begin with |

**Practical implication for CTC head initialization (Section 6)**: when seeding the new Urdu CTC layer from a Hindi-pretrained model's phone embeddings, treat /q/, /x/, /ɣ/ as "warm-start from the nearest Hindi nukta-collapsed phone, then let Urdu fine-tuning data pull them apart" — but treat /ʒ/ as a cold-start class with no useful Hindi initialization available, and budget extra targeted data collection (or G2P-driven TTS augmentation, Section 8) specifically for it if you decide to keep it in the inventory at all.

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

## 12. Project TODO List — Step by Step, From Scratch

Ordered so each phase's outputs feed the next. Checkboxes are for your own tracking. Time estimates assume one focused engineer/researcher plus intermittent SLP/linguist collaboration; clinical-recruitment steps (marked ⏳) are the true critical path and should start in parallel with Phase 0, not after it.

### Phase 0 — Environment, tooling, and linguistic groundwork (Weeks 1–3)

- [ ] Set up a Python environment with `torch`, `torchaudio`, `transformers`, `datasets`, `fairseq` (for IndicWav2Vec/CLSRIL-23 checkpoints), `phonemizer` + `espeak-ng`, `librosa`, `soundfile`, `pyannote.audio` (VAD), `montreal-forced-aligner` (via conda), `onnx`, `onnxruntime`, and `wandb` or similar experiment tracking.
- [ ] Get a GPU environment (local or cloud — A100/L4-class minimum for fine-tuning 300M-parameter encoders in reasonable time; a single consumer GPU with ≥16GB VRAM works for smaller batch fine-tuning).
- [ ] Download and read the **PronouncUR** paper (Sarfraz et al., LREC 2018) and, if available, request/reproduce its Urdu pronunciation lexicon and CISAMPA phoneme table.
- [ ] Build (or obtain) a **Phoible-aligned Urdu IPA phoneme inventory** — cross-reference PronouncUR's CISAMPA set against Phoible's Urdu entry, and produce a single canonical Urdu-IPA phone list (target: ~38–44 phonemes) that you will use as the fixed output vocabulary for every downstream model.
- [ ] Build a **Hindi-phone → Urdu-phone mapping table** by hand (with a linguist if possible): mark 1:1 shared phones, and explicitly flag Urdu-only phones (/ʒ/, /x/, /ɣ/, /q/, aspirated series, nasalized vowels) that Hindi models won't have learned.
- [ ] Stand up a Urdu **G2P** pipeline: start with `espeak-ng`'s Urdu backend via `phonemizer`, validate output against PronouncUR's lexicon on a sample word list, and hand-correct systematic errors into an exceptions dictionary.
- [ ] Design the **phonemically-balanced elicitation word/sentence list** for data collection (Phase 2 and 3): every Urdu phoneme should appear multiple times, in multiple word positions (initial/medial/final), including every aspirated/nasalized/retroflex contrast. Have this list reviewed by an Urdu-speaking SLP or linguist before recording anything.
- [ ] Draft a data-collection consent/ethics protocol (parental consent, child assent where age-appropriate, IRB/ethics-committee submission if working with a hospital/clinic) — submit this **now**, since ethics approval timelines are typically the longest single-item delay in the whole project. ⏳

### Phase 1 — Backbone ASR/phoneme-recognition model on adult Urdu (Weeks 3–7)

- [ ] Download **Common Voice Urdu**, **OpenSLR Urdu corpora**, **Google FLEURS (Urdu split)**, and **IndicSUPERB (Urdu subset)**.
- [ ] Run each dataset's transcripts through your G2P pipeline to produce phoneme-level labels; manually spot-check ~100 outputs for G2P errors before scaling up.
- [ ] Choose your starting checkpoint: **IndicWav2Vec-Large** or **CLSRIL-23** (Hindi-pretrained, Indic-multilingual) as primary candidate; **XLS-R-300M** as fallback/comparison baseline.
- [ ] (Optional but recommended) Run **continual self-supervised pretraining** on unlabeled Urdu audio (Common Voice + OpenSLR, no transcripts needed) for further acoustic adaptation before supervised fine-tuning.
- [ ] Replace the model's output classification layer with a new CTC head sized to your canonical Urdu-IPA phoneme vocabulary (Phase 0); if using a Hindi-pretrained model, initialize shared phones' embeddings from the Hindi head via your phone-mapping table rather than random init.
- [ ] Fine-tune with CTC loss on the combined adult Urdu phoneme-labeled data. Apply SpecAugment + modest speed perturbation (±10%) + VTLP + noise/RIR augmentation during training.
- [ ] Evaluate: **PER** on held-out adult Urdu data; target getting within striking distance of the UltraSuite English reference point (PER ≈ 0.15) as a sanity bound, understanding Urdu + eventual child/disordered speech will likely be harder.
- [ ] Compare **IndicWav2Vec/CLSRIL-23-init** vs. **XLS-R-init** fine-tuning results head-to-head; keep whichever wins on PER as your Phase 2+ base encoder.
- [ ] Freeze this checkpoint as **Backbone-v1**.

### Phase 2 — Typically-developing Urdu child speech collection and adaptation (Weeks 6–14, overlapping Phase 1) ⏳

- [ ] Recruit typically-developing Urdu-speaking children (target: minimum 20–30 children across a spread of ages 4–12, more is better) via schools/community outreach — this does not require clinical/hospital access, only parental consent, so it can start immediately once Phase 0 ethics approval clears.
- [ ] Record each child producing the Phase-0 phonemically-balanced word/sentence list, using consistent recording equipment (target: 16kHz+ sample rate, quiet room, headset or close-mic where possible) and consistent elicitation protocol (picture-naming or repetition, matching how U-TAP/APAC-style Urdu equivalents would be administered if one exists, or design your own analogous task with SLP input).
- [ ] Have a fluent Urdu-speaking transcriber/SLP produce **manual phonetic transcriptions** (not just orthographic) for a subset of this data (target: at minimum 20% of recordings, ideally more) — this becomes your first real Urdu child ground-truth phoneme set and your held-out evaluation set for the rest of the project.
- [ ] Fine-tune Backbone-v1 on this typically-developing child data. Use pitch-shifted adult data (+3 to +6 semitones) and VTLP-augmented adult data as a bridging augmentation strategy alongside the real child data, especially if you have fewer than ~2 hours of real child recordings at this stage.
- [ ] Evaluate PER on the held-out manually-transcribed child subset; iterate on augmentation ratio and learning rate until PER stabilizes.
- [ ] Freeze as **Backbone-v2 (Urdu child-adapted)**.
- [ ] Build the **forced-alignment step**: either adapt Montreal Forced Aligner using your Urdu phoneme set and Backbone-v2 acoustic features, or use Backbone-v2's own CTC posteriors with Viterbi decoding as a lighter-weight aligner if MFA adaptation proves too slow to stand up.

### Phase 3 — Clinical partnership and disordered-speech data collection (Weeks 8–24+, start recruitment as early as ethics approval allows) ⏳

- [ ] Identify and formally partner with 1+ speech therapy clinic, hospital rehabilitation department, or special-education school serving Urdu-speaking children — this is the single highest-risk, highest-lead-time item in the whole project; start outreach in parallel with Phase 0, not after Phase 1/2.
- [ ] Get IRB/ethics approval specific to clinical population recruitment (separate from or an extension of the Phase 0 approval).
- [ ] With partner SLPs, confirm/adapt the elicitation list to match whatever standardized Urdu articulation assessment exists locally, or formally define your own protocol if none does.
- [ ] Record children with SLP-confirmed SSD diagnoses using the same equipment/protocol as Phase 2, plus SLP-provided diagnostic labels (disorder category, severity where available) and, ideally, full manual phonetic transcription for every utterance (this is labor-intensive but is exactly what the Korean 93.6-minute study's strong result depended on — quality manual transcription per minute of audio matters more than raw hours).
- [ ] Target minimum viable dataset: based on the Korean precedent, even ~1.5–2 hours of manually-transcribed disordered child speech (all children combined) is enough to meaningfully fine-tune Stage 2; more is needed specifically for Stage 4 (disorder classification) since that needs examples *per disorder category*, not just examples of "disordered."
- [ ] As data accumulates, log inter-rater reliability between 2+ transcribers on a shared subset (target ICC/Cohen's kappa) — you need this to know how much of your model's disagreement with any single SLP is "model error" vs. normal human transcriber disagreement.

### Phase 4 — Phoneme-recognition fine-tuning on disordered speech (Weeks 16–20, gated on Phase 3 data)

- [ ] Fine-tune Backbone-v2 on the Phase 3 disordered-child data (combined with Phase 2 typical-child data, to avoid the model "unlearning" typical-speech patterns).
- [ ] Evaluate PER against manual transcriptions **separately** for typically-developing vs. disordered subsets, and by rough severity band if labels support it — do not report a single pooled PER.
- [ ] Freeze as **Backbone-v3 (final phoneme-recognition model)**.

### Phase 5 — Error detection module (Weeks 18–22, can start once Backbone-v2 exists, refined with Backbone-v3)

- [ ] Implement forced alignment of each utterance against its G2P-derived expected phoneme sequence.
- [ ] Implement phoneme-level **Levenshtein edit distance** to flag substitutions/deletions/insertions.
- [ ] Implement **logit-based GOP** (GOP_MaxLogit and GOP_Margin) from the CTC head's pre-softmax outputs, per aligned phone segment.
- [ ] Implement a **distinctive-feature mapping** for every Urdu phone (place, manner, voicing, aspiration, nasality) and compute feature-level GOP/confusion in addition to phone-level, to catch aspiration/nasalization-specific errors.
- [ ] Build the **phoneme confusion matrix** from your labeled data (both typical and disordered) as a validation and clinical-interpretability artifact.
- [ ] Calibrate per-phone (or per-feature) GOP thresholds on a validation split; report precision/recall/F1 per error type, not pooled.
- [ ] Validate GOP scores against SLP severity ratings on a held-out subset (compute PCC or similar) — this is your key clinical-credibility check before moving to Stage 6.

### Phase 6 — Disorder classification (Weeks 22–28, gated on sufficient Phase 3 labeled data per category)

- [ ] Start with the simplest viable model: **binary typically-developing vs. disordered** screening classifier, using the Stage 5 error-pattern vector (error-type rates, feature-level error rates) plus basic prosodic features (F0 mean/std, rate, pause statistics) as input to a small model (logistic regression or shallow MLP baseline first, before anything fancier).
- [ ] Add **rule-based phonological-process flags** (fronting, stopping, cluster reduction, etc.) directly from the confusion matrix — this needs no additional labeled disorder data and is useful/interpretable on its own.
- [ ] Once sufficient per-category labeled data exists, build the hierarchical classifier: motor-based (dysarthria/CAS, using prosodic + consistency-across-repetition features) vs. linguistic-based (phonological/articulation/delay, using error-pattern features) branches, each with its own lightweight BiLSTM or small transformer over the per-phone feature sequence.
- [ ] Add multi-task auxiliary heads: age-prediction (forces age-invariant core features) and a speaker-contrastive/adversarial loss (SALR-style, to fight speaker overfitting given small N) alongside the primary disorder-category loss.
- [ ] Evaluate with macro-F1 (primary), per-class ROC-AUC, sensitivity/specificity — reported per disorder subtype, not pooled — and, if feasible, ICC between model severity scores and SLP severity ratings.
- [ ] Only attempt full 5-way (articulation/phonological/CAS/dysarthria/delay) classification once you have a reasonable number of labeled examples in each category; if any category has too few examples, explicitly report that category as "insufficient data, not evaluated" rather than reporting an unreliable number.

### Phase 7 — Evaluation and clinical validation pass (Weeks 26–30)

- [ ] Compile the final evaluation report: PER + alignment accuracy (Stage 2), per-error-type P/R/F1 + confusion matrix + GOP-clinician correlation (Stage 3), macro-F1 + sensitivity/specificity + ICC (Stage 4) — each broken out by typical/disordered and by subtype.
- [ ] Run a **head-to-head comparison session** with your partner SLP(s): have them independently rate a shared held-out set of recordings, compare their ratings to the model's, and report discrepancy counts/patterns (which phonemes/error types the model and humans disagree on most) — this is your most important go/no-go gate before considering any deployment.
- [ ] Write up limitations explicitly: dataset size, demographic coverage (dialects/regions/ages represented), and known failure modes observed during evaluation.

### Phase 8 — Deployment engineering (Weeks 28–34, only after Phase 7 clears an acceptable accuracy bar)

- [ ] Export Backbone-v3 + CTC head to **ONNX**.
- [ ] Apply **post-training INT8 quantization**; re-run the Phase 7 evaluation suite on the quantized model to confirm acceptable accuracy loss before proceeding.
- [ ] (Optional, second-generation) Distill to a smaller (~30–90M parameter) student model; re-evaluate.
- [ ] Benchmark inference latency and memory footprint on your actual target hardware (Jetson Orin Nano preferred; Raspberry Pi 4/5 as budget fallback) using real Urdu child audio samples, not synthetic benchmarks.
- [ ] Implement on-device VAD to gate when the full pipeline runs.
- [ ] Build the interpretable output UI: phoneme-level color-coded error map, per-error-type summary, disorder-likelihood score with confidence, and an explicit "insufficient confidence — refer to SLP" fallback state for low-confidence cases.
- [ ] Decide on-device vs. hybrid-offload architecture (Section 10) based on your final connectivity/privacy/cost constraints, and implement accordingly.
- [ ] Pilot-test the deployed device with your partner clinic on new (not training-set) children, with an SLP reviewing every output during the pilot period before any unsupervised use is considered.

### Ongoing / cross-cutting (all phases)

- [ ] Version and document every dataset, checkpoint, and evaluation result (a simple experiment tracker is sufficient — the goal is being able to answer "which data trained which model got which score" at any point).
- [ ] Revisit the Section 0 constraints periodically: as your own Urdu child SSD corpus grows, consider preparing it for eventual ethical, consented publication — this is a genuine contribution to the field, not just a means to your device.
- [ ] Any time you add a new external claim, benchmark number, or dataset citation to your own documentation, verify it against the primary source before relying on it (see Appendix above) — precise-sounding numbers are the easiest thing to get wrong or inherit wrong from someone else's write-up.

---

## 13. Practical Implementation Notes: HuggingFace Fine-Tuning on a 6GB GPU (RTX 4050)

Verified against the actual `facebook/wav2vec2-xls-r-300m` repo and the standard HF CTC fine-tuning workflow.

### 13a. Why `AutoProcessor`/`AutoModel` on the bare checkpoint isn't the right starting point

- `facebook/wav2vec2-xls-r-300m` ships a feature-extractor config but **no tokenizer files** — `AutoProcessor.from_pretrained(model_id)` will fail with a `Can't load tokenizer... Wav2Vec2CTCTokenizer` error. This is expected, not a bug: the base checkpoint is pretraining-only and deliberately has no output vocabulary baked in.
- `AutoModel.from_pretrained(model_id)` resolves to the bare `Wav2Vec2Model` (encoder only, no CTC head) — usable, but means you'd have to hand-write the CTC head and loss yourself.
- **Use `Wav2Vec2ForCTC` instead of `AutoModel`.** It accepts a `vocab_size` and automatically attaches a correctly-sized, randomly-initialized CTC head (there's no existing head to mismatch against), and computes CTC loss internally when you pass `labels` — this is the standard, well-tested path, not a shortcut.

### 13b. Correct fine-tuning setup

```python
import json
from transformers import (
    Wav2Vec2CTCTokenizer,
    Wav2Vec2FeatureExtractor,
    Wav2Vec2Processor,
    Wav2Vec2ForCTC,
)

model_id = "facebook/wav2vec2-xls-r-300m"

# 1. Build your own vocab.json from the corrected Urdu-IPA phoneme
#    inventory in Section 2a (after you've done the Hussain 2004 /
#    Saleem et al. 2002 reconciliation). Special tokens: [PAD] doubles
#    as the CTC blank token; [UNK] catches anything outside your set.
vocab_dict = {
    # "phoneme_symbol": index, ...
    "[UNK]": 0,
    "[PAD]": 1,
    # | word_delimiter_token only needed if you're doing word-level
    #   phrases, not single-word elicitation items
    "|": 2,
    # ... your ~38-44 Urdu-IPA phonemes start here
}
with open("vocab.json", "w", encoding="utf-8") as f:
    json.dump(vocab_dict, f, ensure_ascii=False)

# 2. Tokenizer from YOUR vocab (not from the base checkpoint, which has none)
tokenizer = Wav2Vec2CTCTokenizer(
    "vocab.json",
    unk_token="[UNK]",
    pad_token="[PAD]",
    word_delimiter_token="|",
)

# 3. Feature extractor DOES load fine from the base checkpoint
#    (preprocessor_config.json exists there)
feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained(model_id)

# 4. Combine into a processor and save it — you'll reuse this exact
#    tokenizer/vocab for every future checkpoint of this project
processor = Wav2Vec2Processor(feature_extractor=feature_extractor, tokenizer=tokenizer)
processor.save_pretrained("./urdu-phoneme-processor")

# 5. Load the model WITH the CTC head sized to your vocab
model = Wav2Vec2ForCTC.from_pretrained(
    model_id,
    ctc_loss_reduction="mean",
    pad_token_id=processor.tokenizer.pad_token_id,
    vocab_size=len(processor.tokenizer),
)
```

### 13c. Fitting 300M-parameter fine-tuning into 6GB VRAM

A 4050 laptop GPU (6GB) is workable for XLS-R-300M fine-tuning but requires all of the following, not just a smaller batch size:

```python
# Freeze the CNN feature encoder (first ~7 conv layers) — this is
# standard practice regardless of VRAM, since these layers encode
# low-level acoustic features that don't need language-specific
# adaptation, and freezing them cuts both memory and overfitting risk
# given your small Urdu dataset.
model.freeze_feature_encoder()
```

- **Mixed precision (fp16/bf16)**: pass `fp16=True` (or `bf16=True` if your driver/CUDA version supports it well on the 4050) to `TrainingArguments` — roughly halves activation memory.
- **Gradient checkpointing**: `model.gradient_checkpointing_enable()` — trades compute for memory by not storing all intermediate activations; essential at this VRAM budget.
- **Small per-device batch size + gradient accumulation**: start with `per_device_train_batch_size=1` or `2` and `gradient_accumulation_steps=8–16` to simulate an effective batch size of ~16–32 without holding it all in memory at once.
- **Cap audio clip length**: truncate/filter training clips to roughly ≤10–15 seconds. Wav2vec2's memory usage scales with raw input length (it processes raw waveform, not fixed-size spectrograms), so a handful of long recordings can spike memory far more than batch size does — for child speech-elicitation data (single words/short phrases) this is rarely a real constraint, but check your longest clips before training.
- **Consider partial layer freezing beyond just the CNN**, if you still hit OOM: freeze the lower half of the 24 Transformer layers as well and only fine-tune the upper layers + new CTC head — reasonable given you likely have far less labeled Urdu data than the original 436k-hour pretraining set, so most of the pretrained representation should be left largely intact anyway.
- **`torch.cuda.amp` autocast** is applied automatically by `Trainer` when `fp16=True`; if you write a custom training loop instead of using `Trainer`, wrap the forward/loss computation in `torch.autocast("cuda", dtype=torch.float16)` yourself.
- **If you still OOM**: drop to fine-tuning `facebook/wav2vec2-xls-r-300m` is already close to the floor for XLS-R itself; the next fallback isn't a smaller XLS-R (300M is the smallest public release) but switching your Section 1 backbone choice to a smaller model class entirely — e.g., `facebook/wav2vec2-base` or a distilled Wav2Vec2 variant — accepting the phonetic-transfer trade-off discussed in Sections 5–6, or renting short bursts of cloud GPU time (e.g. a single A10/L4 instance) specifically for the fine-tuning runs while keeping local development on the 4050.

### 13d. Sanity checks before your first real training run

- [ ] Confirm `len(processor.tokenizer)` matches your intended vocab size exactly (off-by-one errors here silently corrupt every downstream phoneme index).
- [ ] Run a forward pass on one batch and confirm `model(input_values, labels=labels).loss` returns a finite, non-NaN value before committing to a full training run.
- [ ] Log GPU memory (`torch.cuda.max_memory_allocated()`) after your first successful training step to see actual headroom before scaling up batch size or unfreezing more layers.

---

## 14. G2P Implementation Debug Log (findings from actual code review)

Findings from reviewing the working `UrduG2P` implementation (eSpeak-ng `-v ur --ipa` backend + postprocessing/tokenization).

- **Fixed bug**: vocab dict literals used two identical `""` keys intended as separate blank/pad tokens (`"": 56, "": 57`); Python silently collapses duplicate dict-literal keys, producing 57 tokens instead of the intended 58 and merging blank/pad into one token. **No `[UNK]` token exists at all** — any phoneme not already in the vocab is silently dropped in `_tokenize_to_vocab`, not logged. Fix: use distinct non-empty tokens (`"[PAD]"`, `"[UNK]"`), and log/count every dropped character rather than discarding silently.
- **Confirmed design decision, not a bug**: `_postprocess`'s mapping table (`'aː':'ɑ', 'a':'ɑ'`, and the same pattern for o/u/i/e) deliberately collapses every long/short vowel pair to one symbol. This means short/long vowel confusion can never be flagged as an error type downstream — decide explicitly whether that's acceptable for v1 and document it as a known limitation.
- **Likely dead code**: the uppercase ASCII mappings (`'A','E','I','O','U','X','G','N','R'`) and dotted-suffix retroflex mappings (`'t.','d.','n.','r.'`) target eSpeak's internal Kirshenbaum/ASCII notation, which shouldn't appear when `--ipa` is passed to `espeak-ng`. Verify by commenting them out and diffing output on the test set; if unchanged, they're inert.
- **Open question, needs a full-corpus coverage test, not spot-checks**: run the G2P over all of `validated.tsv` and tally per-phoneme occurrence counts. Suspect `/q/` (eSpeak's rule-based Urdu synthesis likely doesn't distinguish ق from ک) and the nasalized-vowel set may have zero or near-zero occurrences — if so, no amount of downstream fine-tuning fixes that; it's a G2P coverage gap to know about before spending training time.
- **Corpus size sanity check (independent confirmation of Section 7 numbers)**: Kathbath/IndicSUPERB Urdu = 49,201 train + 3,229 valid utterances ≈ 87.4h at typical utterance length, matching the 86.7h figure already in Section 7. FLEURS `ur_pk` = 2,109+267+299 = 2,675 utterances ≈ 10h, also matching. Good sign the downloaded data matches the expected corpora rather than a mislabeled subset.

---

## 15. G2P Coverage Analysis (from ~900-word smoke test on live pipeline)

Findings from tallying phoneme occurrences across a large eSpeak-ng-based Urdu G2P test run, after the `[PAD]`/`[UNK]` fix from Section 14 was applied (confirmed working — it correctly surfaced real gaps like `جذبہ → dʒ ɑ [UNK] b ɑ` instead of silently dropping them).

- **Confirmed dead phoneme: retroflex flap /ɽ/.** Zero occurrences across ~900 words despite ڑ appearing dozens of times (`کھڑا, بڑا, پڑھنا, دوڑنا, چڑیا`, etc.) — eSpeak's Urdu voice appears to collapse ڑ to plain `/r/` universally. This is a real, clinically-relevant Urdu contrast that's currently absent from every training label produced by this pipeline.
- **Confirmed dead phoneme class: all 8 nasalized vowels.** Zero occurrences. Nasalization is represented (if at all) as a following plain `/n/` consonant, never as vowel nasalization (`کان → k ɑ n`, not a nasalized vowel + n).
- **Correction to a prior hypothesis**: `/q/` was predicted as likely rare/absent; the actual test shows it's well-preserved across many words (`قلم, قرآن, حق, طاقتور`, etc.) — worth remembering that predictions here should be tested, not assumed, in either direction.
- **Arabic liturgical/honorific phrases produce badly broken output** (`عبده`, `ورسوله`, and similar Classical Arabic honorific strings) — recommend excluding this vocabulary cluster from training data entirely; it's both the worst-performing and least relevant content for a pediatric articulation-assessment tool.
- **Source word-list data-quality issue (not a pipeline bug)**: several nominally-Urdu entries contain embedded Latin-script fragments (`ادrak, رahim, گaram, پudina, ulta`), which `_normalize`'s Arabic-block-only regex correctly strips, silently producing truncated or empty output. Add an explicit pre-G2P validation step flagging any string containing `[a-zA-Z]`.
- **Possible systematic mismapping on ص (sād)**: rendered as `/ʃ/` in at least two tested words (`غصہ, عصمت`) where naturalized Urdu pronunciation typically uses `/s/`. Worth a native-speaker check since it could affect a meaningful slice of Perso-Arabic vocabulary.

**Recommended fix for the two confirmed dead phonemes**: don't wait on eSpeak. Both ڑ and ں are unambiguous at the grapheme level in Urdu script — add a targeted grapheme-level override in `_postprocess` (before or independent of the eSpeak IPA stream) that forces ڑ → `ɽ` and treats ں as a reliable trigger to mark the preceding vowel's nasalized variant, rather than trusting eSpeak's phonetic realization for exactly the two places it's been shown to fail. This is narrower and faster than switching the whole G2P to a PronouncUR-based lexicon, while directly fixing the two confirmed gaps.

**Process note**: this kind of full-corpus tally (not spot-checking 8–10 words) is what actually surfaces these gaps — recommend automating it as a standing script (`Counter` over all output tokens across `validated.tsv`) that reruns any time the G2P mapping table changes, rather than re-checking by eye each time.

---

## 16. Grapheme-Level Overrides — Working Code (ڑ→ɽ, ں-nasalization) + Audit Tools

Implements the fix recommended in Section 15. Verified working on synthetic test cases (`کھڑا`/`بڑا` correctly get `ɽ`; `گاؤں` correctly nasalizes to `õ`; `ادrak` correctly flagged as mixed-script). Full code with wiring instructions: see `urdu_g2p_patches.py` alongside this document. Contents summary:

- `apply_retroflex_override(original_text, tokens)` — positionally aligns ر/ڑ graphemes in the source text against `'r'` tokens in the output; forces retroflex positions to `ɽ`. Safety: if grapheme count and token count don't match (eSpeak deleted/inserted a segment), it skips that word and logs a warning rather than guessing.
- `apply_nasalization_override(original_text, tokens)` — if the source word contains ں (noon ghunna, distinct from regular ن), nasalizes the last oral-vowel token found. Heuristic covers the dominant word-final case (`گاؤں, ہندوؤں, میں, کہاں`); mid-word ں isn't specially handled yet.
- `flag_mixed_script(text)` / `audit_word_list(words)` — flags nominally-Urdu strings containing Latin `a-zA-Z` characters (catches contamination like `ادrak`, `رahim`, `ulta`).
- `audit_phoneme_coverage(tsv_path, g2p, vocab)` — runs G2P over an entire Common Voice-style TSV and tallies real per-phoneme occurrence counts via `collections.Counter`, reporting any phoneme with zero coverage. This is the automated version of the manual ~900-word tally from Section 15 — run it after applying the overrides to confirm the fix lands at full corpus scale, not just on hand-picked words.

**Required change to `urdug2p.py`**: `_tokenize_to_vocab` must return the token **list**, not the joined string, so the overrides can index into it positionally before final `' '.join()`.

---

## 17. Aspirated Retroflex Flap /ɽʰ/ Fix (found via large-scale regression test)

Running the fixed G2P over ~350 real words (vs. the original ~10-word regression set) confirmed both Section 16 fixes hold up at scale with no regressions, including on a genuine mixed-case word not in the original test set (`کروڑ` — medial plain ر + final ڑ — correctly resolves to `k ə r o ɽ`, exactly as it should).

It also surfaced a new, real gap: `داڑھی` (beard) contains ڑ immediately followed by ھ (aspiration marker), i.e. the **aspirated retroflex flap /ɽʰ/** flagged as a possible missing phone back in Section 2a — now confirmed to occur in actual child-relevant vocabulary. It was coming out as two separate tokens (`ɽ`, `h`) instead of one.

**Fix required care about pipeline ordering, not just adding a rule.** The other aspirated consonants (`pʰ, bʰ, tʰ, ʈʰ, ɖʰ, kʰ, gʰ, tʃʰ, dʒʰ`) all get collapsed early, in `_postprocess`, because eSpeak emits their plain forms directly in its raw output. `/ɽ/` is different: eSpeak has no concept of the retroflex flap at all and always emits plain `r`, so at `_postprocess` time (which runs before tokenization and before our own retroflex override) there is no `ɽ` token yet to collapse with a following `h` — a first attempt at fixing this by adding `('ɽ h', 'ɽʰ')` to the `_postprocess` replacement list was tested and confirmed to be dead code, since it fires before the override that would ever produce an `ɽ` in the first place.

**Correct fix**: added `ɽʰ` to the vocab, and a new `_merge_retroflex_aspiration(tokens)` step that runs on the token list *after* `_apply_retroflex_override` (once `ɽ` tokens actually exist), merging any `['ɽ', 'h']` pair into a single `'ɽʰ'` token. Verified against a mocked eSpeak output for `داڑھی` — now correctly returns `d ɑ ɽʰ i`.

**Recurring, not new**: ص consistently renders as `/ʃ/` across an increasing number of examples (`صدقہ, صبح, صحرا, صفر, غصہ, عصمت`) — frequent enough now to look systematic rather than incidental, still pending a native-speaker check.

---

## 18. Root Cause of the Near-Universal Word/Segment Mismatch: Cross-Word Aspiration Corruption

Running the coverage audit (Section 16 tooling) on 5000 real Common Voice sentences surfaced word/segment mismatch warnings on the large majority of sentences — far too many to be the rare edge case the fallback was designed for. Initial hypothesis (standalone punctuation as fake "words") was tested and found insufficient: `آج دھوپ ہے` ("today is sunny") has zero punctuation and still mismatched (3 words vs 2 segments).

**Actual root cause, confirmed against real eSpeak output** (not mocked): `_postprocess`'s aspiration-collapse rules (`('p h', 'pʰ')`, `('t h', 'tʰ')`, etc.) operated on the *entire raw string* with plain `.replace()`, with no concept of word boundaries. eSpeak's real raw output for `آج دھوپ ہے` is `'ˈaːɟ dʰˈoːp hɛ'` — three cleanly space-separated words. But because the second word ends in `p` and the third word (`ہے`, "is/are" — one of the single most common words in Urdu) starts with `h`, the rule `('p h', 'pʰ')` fired **across the word boundary**, deleting the space and fabricating a `pʰ` that was never in the source audio: postprocessed result was `'dʰopʰɛ'` instead of the correct `'dʰop hɛ'`. Every one of the four diagnosed mismatch examples traced to this exact mechanism. Given how frequent `ہے` (and similar h-initial function words) is in everyday Urdu, this wasn't a rare edge case — it corrupted a large fraction of real multi-word training labels, both by destroying word-boundary information *and* by inserting phantom aspirated consonants while deleting real ones.

**Fix**: moved both the `sorted_mappings` replacements and the aspiration-collapse rules to run **per word** (split on whitespace first, process each word independently, rejoin with single spaces) instead of on the whole string at once. Verified directly against the real (not mocked) eSpeak output the user captured: all previously-mismatching examples now correctly match word count to segment count, and the phoneme content itself is now correct (`دھوپ ہے → dʰ o p | h ɛ`, keeping `p` and `h` properly separate).

**Process note worth keeping**: this bug was invisible in every single-word regression test run so far, precisely because it only manifests at a word *boundary* — a reminder that fixes validated only on isolated words or small hand-picked phrases can hide boundary-spanning bugs that only surface at corpus scale. The coverage audit tooling (Section 16) built specifically to catch this kind of thing is what surfaced it.

**Remaining expected mismatches after this fix**: sentences containing standalone punctuation, stray diacritics, or tatweel elongation marks as isolated "words" (observed in the audit: `ـ`, `ِ`, `ً` appearing alone) will still legitimately mismatch, since eSpeak produces zero phonemes for these — this is a genuine data-quality characteristic of crowd-sourced Common Voice text (including a notable amount of classical Urdu poetry with pen-name markers like `ؔ` and izafat marks like `ٴ`), not a G2P bug, and is reasonable to leave as sentence-wide fallback or to filter at the manifest-building stage (Section 12/16).
