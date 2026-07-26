# Doc C — Model Training, Fine-Tuning & Evaluation Engineering
### Urdu Child Speech-Disorder Assessment Pipeline (3 of 4)

*Third of four documents. Covers the actual CTC fine-tuning setup, the real training run (including a costly checkpoint-resume bug and how it was fixed), held-out test evaluation, the forced-alignment + GOP scoring pipeline, and the ongoing Hindi-backbone comparison experiment. Everything in this document reflects what actually happened during training, not just the plan — including the bugs found along the way, since those are as important to keep on record as the successes. See Doc A for research design, Doc B for G2P engineering, and Doc D for the project roadmap.*

---

## 1. Fine-Tuning Setup: HuggingFace CTC Training on a 6GB GPU (RTX 4050)

Verified against the actual `facebook/wav2vec2-xls-r-300m` repo and the standard HF CTC fine-tuning workflow.

### 1a. Why `AutoProcessor`/`AutoModel` on the bare checkpoint isn't the right starting point

- `facebook/wav2vec2-xls-r-300m` ships a feature-extractor config but **no tokenizer files** — `AutoProcessor.from_pretrained(model_id)` will fail with a `Can't load tokenizer... Wav2Vec2CTCTokenizer` error. This is expected, not a bug: the base checkpoint is pretraining-only and deliberately has no output vocabulary baked in.
- `AutoModel.from_pretrained(model_id)` resolves to the bare `Wav2Vec2Model` (encoder only, no CTC head) — usable, but means you'd have to hand-write the CTC head and loss yourself.
- **Use `Wav2Vec2ForCTC` instead of `AutoModel`.** It accepts a `vocab_size` and automatically attaches a correctly-sized, randomly-initialized CTC head (there's no existing head to mismatch against), and computes CTC loss internally when you pass `labels` — this is the standard, well-tested path, not a shortcut.

### 1b. Correct fine-tuning setup

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

### 1c. Fitting 300M-parameter fine-tuning into 6GB VRAM

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

### 1d. Sanity checks before your first real training run

- [ ] Confirm `len(processor.tokenizer)` matches your intended vocab size exactly (off-by-one errors here silently corrupt every downstream phoneme index).
- [ ] Run a forward pass on one batch and confirm `model(input_values, labels=labels).loss` returns a finite, non-NaN value before committing to a full training run.
- [ ] Log GPU memory (`torch.cuda.max_memory_allocated()`) after your first successful training step to see actual headroom before scaling up batch size or unfreezing more layers.

---


---

## 2. The Actual XLS-R Backbone-v1 Training Run (a journal, including the bugs)

This section documents what actually happened during the real training run, not just the plan — including two costly mistakes and how they were caught, because both are worth remembering for every future training run on this project.

### 2a. Bug 1: `eval_loss: inf` — the CTC length-mismatch problem

Partway through the first training attempt, the health-check metric (`eval_loss`) came back as `inf` instead of a real number. Root cause: CTC requires the model's output frame count (raw audio samples divided by ~320, wav2vec2/XLS-R's CNN downsampling factor) to exceed the label's phoneme count for every utterance — the same way you need at least as many parking spaces as cars. A handful of clips in the dataset were too short (probably clipped recordings) to satisfy this for their label length, which is mathematically impossible to score, and by default a single such impossible example poisons the *entire* averaged loss, not just its own row.

**Fix, two parts**:
1. `ctc_zero_infinity=True` passed to `Wav2Vec2ForCTC.from_pretrained(...)` — HuggingFace's own documented mechanism to zero out an individual pathological example's loss instead of letting it corrupt the batch/epoch average. A safety net, not the real fix.
2. `filter_ctc_length()` — a dataset filter removing any example where `input_length // 320 <= len(labels)`, applied to **both** train and dev splits before training. This is the actual root-cause fix: those examples were likely also silently contributing zero-value or corrupted gradient steps during training itself, not just breaking the eval number.

A proper PER (Phoneme Error Rate) metric was also added at this point — the original script had no `compute_metrics` at all, meaning the only visible signal was raw CTC loss, which isn't interpretable on its own (is 8.3 good or bad? no way to tell without a real metric).

### 2b. Bug 2: the hardcoded checkpoint path — a costly mistake

A more serious mistake, and one worth being honest about since it cost real GPU time: the fix for Bug 1 included resuming training via
```python
RESUME_CHECKPOINT = os.path.join(OUTPUT_DIR, "checkpoint-400")
trainer.train(resume_from_checkpoint=RESUME_CHECKPOINT)
```
This was correct **at the time** — checkpoint-400 genuinely was the latest checkpoint right after the `eval_loss: inf` incident. But it was hardcoded as a literal string, not looked up dynamically. When the training process was later restarted (after having already progressed to step ~3027 of 4560, epoch 6.58, with `eval_per` already down to 0.1897), the script blindly jumped back to checkpoint-400 again, discarding all progress made between those two points — several hours of real training time.

By the time this was caught, `save_total_limit=2` had already pruned checkpoint-400 itself in some runs and the actual best-remaining checkpoint on disk turned out to be checkpoint-800. Training had to resume from there and re-traverse epochs that had already been learned once.

**Permanent fix — never hardcode a checkpoint path again**:
```python
resume = True if os.path.isdir(OUTPUT_DIR) and any(
    d.startswith("checkpoint-") for d in os.listdir(OUTPUT_DIR)
) else None
trainer.train(resume_from_checkpoint=resume)
```
Passing `True` (not a path string) tells `Trainer` to find the actual latest checkpoint in `output_dir` itself, every time. This logic was tested against three cases (fresh start with no output dir, an empty output dir, and a dir with real checkpoints) before being trusted, and should be the standard pattern for every future training script in this project, including the Hindi-backbone comparison (Section 5 below).

### 2c. Final result

Despite the checkpoint mixup costing wall-clock time, it didn't cost final quality — because the resumed run continued all the way to a complete 10 epochs, the final model ended up at least as good as where the original (interrupted) trajectory had been heading:

| Epoch | eval_loss | eval_per |
|---|---|---|
| 1.756 | 1.118 | 0.2861 |
| 2.633 | 0.9518 | 0.2400 |
| 3.51 | 0.8642 | 0.2185 |
| 4.387 | 0.8172 | 0.2035 |
| 5.264 | 0.8223 | 0.1984 |
| 6.141 | 0.7894 | 0.1897 |
| 7.896 | 0.7816 | 0.1791 |
| 8.773 | 0.7595 | 0.1747 |
| 9.65 | 0.7654 | 0.1723 |
| 10 (final) | 0.7625 | **0.1718** |

PER dropped smoothly and consistently the whole way, with the rate of improvement shrinking near the end (classic, healthy convergence signature — not stopped mid-improvement, not overfitting either, since `eval_loss` never diverged upward while PER kept improving). This model is referred to elsewhere as **Backbone-v1**, saved at `urdu_xls_r_phoneme/`.

---

## 3. Held-Out Test Set Evaluation

Dev-set PER was implicitly "peeked at" throughout training (used to judge health, decide when convergence was reached). The honest, unbiased number comes from a completely untouched test split.

**Result: 13.21% PER on 5,026 held-out test utterances** — actually a little better than the final dev PER (17.18%), plausibly because dev was indirectly influencing decisions throughout training while test never was, and/or the test split happening to be marginally easier on average.

### 3a. A bug found via the "10 worst utterances" diagnostic

Printing the worst-performing utterances (not just the aggregate score) surfaced a clear, useful pattern: most of the worst cases were **long reference utterances collapsing into a tiny handful of tokens, mostly `/ɑ/` repeated** — e.g. a 12-phoneme reference producing just `ɑ ɑ` as output. `/ɑ/` is by a wide margin the single most frequent phoneme in the training vocabulary (~25,000 occurrences in the coverage audit, more than double the next most common), which is exactly what a CTC model defaults to when it structurally cannot produce enough output for the label length — the same length-mismatch problem as Bug 1 above, just manifesting at evaluation time instead of training time.

**Root cause**: the `filter_ctc_length()` filter had been applied to train and dev, but the evaluation script never had it applied to the **test** set. Fixed by adding the identical filter before evaluating. With roughly 10 pathological examples out of 5,026 (~0.2%), this doesn't move the aggregate PER much, but it matters for trusting the "worst utterances" diagnostic list, and for not mistaking a mathematically-impossible example for a genuine model weakness.

One separate worst-case (`PER=1.00`, the entire reference sentence appearing twice in the hypothesis) was diagnosed differently: greedy CTC decoding is frame-independent and structurally cannot invent a repeat on its own, so this almost certainly reflects the *source audio itself* containing the sentence spoken twice (a known Common Voice crowd-sourcing quality issue — a contributor re-recording without trimming the first attempt), not a pipeline bug.

**Practical lesson for later**: if a long child utterance ever collapses into a handful of `/ɑ/`s during real assessment, the first diagnostic instinct should be "check audio length against label length," not "the model failed to understand this word."

---

## 4. Forced Alignment + GOP Scoring Pipeline

This is the piece that turns "a phoneme recognizer" into an actual error-detection tool — Section 3/13 of Doc A's theoretical design, implemented and tested.

### 4a. What it does

Given an audio file and its expected phoneme sequence (from the G2P tool in Doc B), it:
1. Runs Backbone-v1 to get per-frame logits.
2. Does CTC Viterbi forced alignment against the expected sequence.
3. Computes GOP_MaxLogit and GOP_Margin per phone.
4. Flags any phone with negative GOP_Margin as likely mispronounced.

### 4b. A real bug caught before it shipped: the geminate/repeated-phone case

The first draft grouped aligned frames by **phone value** (does this frame's label match phone X?). This silently breaks on any word with two identical phones adjacent to each other — verified directly with a synthetic test: for a sequence like `l-l`, it dumped all frames from *both* `l`s into the first one's segment, leaving the second with zero frames. Urdu has plenty of these (`بلی`, `غصہ→ɣʊʃʃɑ`, reduplicated words like `کھڑکھڑا`), so this would have quietly corrupted GOP scores across a meaningful slice of vocabulary.

**Fix**: track exact **position** in the CTC lattice instead of phone value — position has no such ambiguity even when two neighboring phones are identical (original label index `i` sits at extended-sequence position `2i+1` by construction). Re-verified against both the failing and passing cases before trusting it.

### 4c. Verification performed before use

- Synthetic ground-truth alignment test (simple non-repeated case): passed.
- Synthetic repeated-adjacent-phone (geminate) test: failed on first attempt, fixed, passed on retest.
- GOP scoring test: confirmed positive margin for a confidently-correct synthetic case, negative margin for a case where a competing phone dominates — the exact discrimination the tool needs to make.
- Full end-to-end integration test (alignment → grouping → GOP) on a simulated geminate word with a deliberately weaker second repeated phone: correctly assigned a lower GOP score to the weaker instance.

### 4d. Convenience integration

The consolidated script accepts either plain Urdu text (runs your G2P automatically) or a pre-tokenized phoneme string (`--raw-phonemes` flag), checks for `[UNK]` tokens in the G2P output before scoring, and sanity-checks audio length against label length up front (same length-mismatch problem as Sections 2a/3a, caught here too before attempting an alignment that can't mathematically exist).

### 4e. Calibration warning

`GOP_FLAG_THRESHOLD = 0.0` is a reasonable **starting point**, not a validated clinical threshold. Per Doc A Section 9, calibrate this against a small set of recordings with known correct/incorrect pronunciations before trusting it for anything resembling real assessment — say some words correctly, then deliberately mispronounce the same words, and confirm the GOP scores actually separate the two cases sensibly.

---

## 5. Hindi-Backbone Comparison Experiment — RESULT: Hindi backbone wins, now the primary Backbone-v1

Testing the Hindi-Urdu phonetic-transfer hypothesis from Doc A, Sections 5-6, empirically: does initializing from a Hindi-pretrained model produce a better Urdu phoneme recognizer than generic multilingual XLS-R, given the closer phonetic cluster match (Hindi/Urdu/Punjabi/Sanskrit)?

**Setup**:
- Model: `ai4bharat/indicwav2vec-hindi` (a gated HuggingFace repo — required accepting the repo's conditions once, same as the earlier Kathbath dataset).
- Reused the **exact same** `hf_dataset/{train,dev,test}` built for the XLS-R run — the Urdu phoneme labels are independent of which acoustic backbone consumes them, and wav2vec2-family feature extraction is essentially identical across all wav2vec2-style models.
- `ignore_mismatched_sizes=True` was required: unlike XLS-R-300M (no classification head at all), this checkpoint already had a working head sized for Hindi ASR output (confirmed in the load report: `weight | MISMATCH | Reinit due to size mismatch - ckpt: torch.Size([68, 1024]) vs model: torch.Size([61, 1024])`); this flag tells HuggingFace to discard it and initialize a fresh head sized to the Urdu phoneme vocabulary instead of erroring.
- Used the corrected dynamic checkpoint-resume logic from Section 2b — no repeat of the hardcoded-checkpoint mistake.
- Trained into a separate output directory (`urdu_indicwav2vec_hindi_phoneme/`), keeping the XLS-R checkpoints untouched.

### Result: decisive win for the Hindi-pretrained backbone

| Metric | XLS-R-300M (Backbone-v1, original) | IndicWav2Vec-Hindi (Backbone-v1, current) |
|---|---|---|
| Final dev PER (epoch 10) | 17.18% | **13.73%** |
| Final held-out test PER | 13.21% | **9.47%** |
| Relative improvement | — | ~28% lower test PER |

At comparable epochs throughout training, the Hindi backbone was ahead at *every single checkpoint*, not just at the end — by epoch 6, it had already surpassed XLS-R's fully-converged epoch-10 result. This is a clear, direct empirical confirmation of the Hindi-Urdu phonetic-transfer argument from Doc A: starting from a model with existing instincts for the Hindi/Urdu/Punjabi/Sanskrit phonetic cluster measurably outperformed generic multilingual pretraining for this task.

**Decision: the IndicWav2Vec-Hindi fine-tune is now the primary Backbone-v1**, saved at `urdu_indicwav2vec_hindi_phoneme/`, superseding the XLS-R version for all downstream work (GOP pipeline, future child-data fine-tuning, etc.). The XLS-R checkpoint is kept on disk as a fallback/reference, not deleted.

### A useful diagnostic from the worst-case analysis

Cross-checking the "10 worst utterances" list between the two models' test evaluations showed substantial overlap — several of the same specific clips (including the single worst-performing utterance in both cases, and a case where the reference sentence appears duplicated in the hypothesis) appeared as worst-performers for **both** independently-trained models. Two very differently-trained models producing the same failure pattern on the same clip is strong evidence these are genuine **source-data problems** (audio-transcript mismatches, or in the duplication case, likely a genuine duplicate-take recording never trimmed by the original Common Voice contributor) rather than a weakness in either model. Worth spot-checking a few of these by ear and considering excluding them from future manifests, since they're adding noise to the PER metric rather than reflecting real model quality.

### One operational anomaly noted during this run, unresolved

A single eval pass at epoch 9.65 took ~8.5 hours (`eval_runtime: 3.062e+04` seconds) versus a normal ~25 minutes for every other eval in the run — roughly a 20x slowdown, though it didn't affect the correctness of the result (PER kept improving smoothly through it). Leading hypotheses: Windows Defender real-time scanning interference, or a cloud-sync conflict if any data directories are inside a synced folder. Worth a quick check before the next long training run (child-data fine-tuning), since 8+ hours of unexplained stall is expensive to keep absorbing silently.
