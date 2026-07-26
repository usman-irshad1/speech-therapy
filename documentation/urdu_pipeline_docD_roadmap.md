# Doc D — Project Roadmap & Status
### Urdu Child Speech-Disorder Assessment Pipeline (4 of 4)

*Fourth of four documents. This is the original phased project plan, with checkboxes updated to reflect what's actually been done, what was skipped or done differently, and what's still outstanding. See Doc A for research design, Doc B for G2P engineering, and Doc C for model training engineering. For a detailed forward-looking plan on what to do right now, see the separate "Next Steps" document.*

---

## Current Status Summary (as of this writing)

**Done:**
- Urdu phoneme inventory finalized and verified (Doc B, Section 2a).
- G2P pipeline built, debugged, and verified at corpus scale (Doc B).
- Phase 0 and most of Phase 1 (adult-data backbone) complete.
- **Backbone-v1 trained, compared, and finalized: IndicWav2Vec-Hindi wins decisively over XLS-R-300M** (Doc C, Sections 2-3, 5).
  - XLS-R-300M: 13.21% test PER (kept as fallback/reference, not deleted).
  - **IndicWav2Vec-Hindi: 9.47% test PER — ~28% relative improvement, now the primary Backbone-v1** at `urdu_indicwav2vec_hindi_phoneme/`. This is a direct empirical confirmation of the Hindi-Urdu phonetic-transfer hypothesis from Doc A, Sections 5-6 — not just a theoretical argument anymore.
- Forced alignment + GOP scoring pipeline built and verified (Doc C, Section 4) — should now be repointed at the Hindi backbone for all future use.

**Not yet started (the actual bottleneck):**
- Phase 0's elicitation word list (needed before any child recording can start).
- Phase 0/3's ethics/consent protocol.
- **Phase 2**: recording typically-developing Urdu-speaking children.
- **Phase 3**: clinical partnership for disordered-speech data — the single longest-lead-time item in the entire project.
- Phases 4-8 (disordered-speech fine-tuning, disorder classification, deployment) are all gated on Phase 3 data existing.

**Skipped or done differently than originally planned** (noted inline below, search for "skipped" or "not actually applied"):
- Continual self-supervised pretraining before fine-tuning.
- Data augmentation (SpecAugment, VTLP, noise injection) during Backbone-v1 training.
- Phone-mapping-informed CTC head initialization for the Hindi backbone (used random init instead via `ignore_mismatched_sizes=True`) — worth noting the backbone won decisively even without this refinement, suggesting the phonetic-cluster pretraining alone carries most of the benefit.

**Worth a quick follow-up, low priority**: several of the worst-performing test utterances were identical across both backbones' evaluations (including one showing a duplicated-sentence hallucination in both), suggesting genuine source-data problems (bad transcripts, an untrimmed duplicate-take recording) rather than model weaknesses — worth spot-checking by ear and excluding from future manifests if confirmed.

---

## Project TODO List — Step by Step, From Scratch (Updated Status)

Ordered so each phase's outputs feed the next. Checkboxes are for your own tracking. Time estimates assume one focused engineer/researcher plus intermittent SLP/linguist collaboration; clinical-recruitment steps (marked ⏳) are the true critical path and should start in parallel with Phase 0, not after it.

### Phase 0 — Environment, tooling, and linguistic groundwork (Weeks 1–3)

- [x] Set up a Python environment with `torch`, `torchaudio`, `transformers`, `datasets` (for IndicWav2Vec/CLSRIL-23 checkpoints), `phonemizer` + `espeak-ng`, `librosa`, `soundfile`, `pyannote.audio` (VAD), `montreal-forced-aligner` (via conda), `onnx`, `onnxruntime`, and `wandb` or similar experiment tracking.
- [x] Get a GPU environment — used a local RTX 4050 (6GB VRAM) rather than cloud A100/L4; required the VRAM mitigations in Doc C Section 1 — A100/L4-class minimum for fine-tuning 300M-parameter encoders in reasonable time; a single consumer GPU with ≥16GB VRAM works for smaller batch fine-tuning).
- [x] Download and read the **PronouncUR** paper (Sarfraz et al., LREC 2018) and, if available, request/reproduce its Urdu pronunciation lexicon and CISAMPA phoneme table.
- [x] Build a Urdu IPA phoneme inventory — see Doc B Section 2a for the corrected, verified 59-token version (removed a non-phonemic retroflex nasal, added the aspirated retroflex flap /ɽʰ/ after finding it needed in real vocabulary) — cross-reference PronouncUR's CISAMPA set against Phoible's Urdu entry, and produce a single canonical Urdu-IPA phone list (target: ~38–44 phonemes) that you will use as the fixed output vocabulary for every downstream model.
- [x] Build a Hindi-phone → Urdu-phone mapping table — see Doc B Section 2b (with a linguist if possible): mark 1:1 shared phones, and explicitly flag Urdu-only phones (/ʒ/, /x/, /ɣ/, /q/, aspirated series, nasalized vowels) that Hindi models won't have learned.
- [x] Stand up a Urdu G2P pipeline (espeak-ng + extensive hand-corrections) — this took far more debugging than originally planned; see Doc B for the full saga (word-boundary bugs, retroflex/nasalization overrides, the geminate case, etc.) via `phonemizer`, validate output against PronouncUR's lexicon on a sample word list, and hand-correct systematic errors into an exceptions dictionary.
- [ ] Design the phonemically-balanced elicitation word/sentence list — **not yet done**, still needed before Phase 2 recording can start for data collection (Phase 2 and 3): every Urdu phoneme should appear multiple times, in multiple word positions (initial/medial/final), including every aspirated/nasalized/retroflex contrast. Have this list reviewed by an Urdu-speaking SLP or linguist before recording anything.
- [ ] Draft a data-collection consent/ethics protocol — **status unconfirmed, this is the actual critical-path item, see the separate forward-plan document** (parental consent, child assent where age-appropriate, IRB/ethics-committee submission if working with a hospital/clinic) — submit this **now**, since ethics approval timelines are typically the longest single-item delay in the whole project. ⏳

### Phase 1 — Backbone ASR/phoneme-recognition model on adult Urdu (Weeks 3–7)

- [x] Download Common Voice Urdu, Google FLEURS (Urdu), and Kathbath/IndicSUPERB (Urdu) — OpenSLR not used, the three above were sufficient, **Google FLEURS (Urdu split)**, and **IndicSUPERB (Urdu subset)**.
- [x] Run all transcripts through the G2P pipeline, spot-checked extensively (900+ word smoke test, then full-corpus coverage audits) — built manifests, dropped ~1% of rows with genuine [UNK]/mixed-script issues rather than keeping wrong labels to produce phoneme-level labels; manually spot-check ~100 outputs for G2P errors before scaling up.
- [x] Chose XLS-R-300M as the first backbone (not IndicWav2Vec/CLSRIL-23 first, contrary to the original plan's stated preference) — the Hindi-pretrained comparison (IndicWav2Vec-Hindi) is now being run separately, see Doc C Section 5 (Hindi-pretrained, Indic-multilingual) as primary candidate; **XLS-R-300M** as fallback/comparison baseline.
- [ ] Continual self-supervised pretraining — **skipped**, went straight to supervised fine-tuning; worth revisiting if further PER gains are needed later on unlabeled Urdu audio (Common Voice + OpenSLR, no transcripts needed) for further acoustic adaptation before supervised fine-tuning.
- [x] Replaced the output layer with a CTC head sized to the Urdu phoneme vocabulary (`Wav2Vec2ForCTC` with `vocab_size=...`) — note: for XLS-R this was a fresh random-init head (no Hindi head to inherit from); for the Hindi-backbone run, `ignore_mismatched_sizes=True` discards the existing Hindi-sized head and randomly initializes a new one (the phone-mapping-informed initialization described in the original plan was not implemented — a possible future refinement) with a new CTC head sized to your canonical Urdu-IPA phoneme vocabulary (Phase 0); if using a Hindi-pretrained model, initialize shared phones' embeddings from the Hindi head via your phone-mapping table rather than random init.
- [x] Fine-tuned with CTC loss on the combined adult Urdu data — note: SpecAugment/speed perturbation/VTLP/noise augmentation described in the original plan were **not actually applied**; training used raw audio only. Worth adding if PER needs to improve further, especially before child-speech fine-tuning where the adult-to-child acoustic gap is real + modest speed perturbation (±10%) + VTLP + noise/RIR augmentation during training.
- [x] Evaluated PER on held-out **test** data (not just dev): **13.21% final test PER** for the XLS-R backbone. Not directly comparable to UltraSuite's 0.15 English benchmark (different language, different data source), but a solid result for a first Urdu phoneme-recognition pass; target getting within striking distance of the UltraSuite English reference point (PER ≈ 0.15) as a sanity bound, understanding Urdu + eventual child/disordered speech will likely be harder.
- [x] Compare IndicWav2Vec-Hindi-init vs. XLS-R-init head-to-head — **IndicWav2Vec-Hindi wins clearly (9.47% vs 13.21% test PER)**, see Doc C Section 5. This is now the Phase 2+ base encoder.
- [x] Froze the XLS-R fine-tune as **Backbone-v1**, saved at `urdu_xls_r_phoneme/`

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

