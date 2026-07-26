# Next Steps Plan — Urdu Child Speech-Disorder Pipeline

*Companion to the 4-document set (Docs A-D). This is the forward-looking action plan from where the project stands right now: Backbone-v1 finalized as the IndicWav2Vec-Hindi fine-tune (9.47% test PER, decisively beating the earlier XLS-R attempt at 13.21%), GOP/forced-alignment pipeline built and verified, ready to be repointed at the new backbone.*

---

## Immediate (this week)

### 1. Repoint everything at the new Backbone-v1, and clean up the test-set noise
- The Hindi-backbone comparison is **done**: IndicWav2Vec-Hindi wins decisively (9.47% vs 13.21% test PER). It's now the primary Backbone-v1, at `urdu_indicwav2vec_hindi_phoneme/`.
- Update `MODEL_DIR` in `gop_pipeline.py` to point at this backbone before doing anything else with it — it was still pointing at the XLS-R output.
- Spot-check (by ear) the small handful of test clips that both backbones independently failed on identically (Doc C Section 5 has the list) — if confirmed as bad source data (mismatched transcript or an untrimmed duplicate-take recording), exclude them from future manifests so they stop adding noise to your metrics.
- Optional, low priority: investigate the ~8.5-hour eval stall noted during the Hindi-backbone training run (Doc C Section 5) before your next long run — likely a Windows Defender or cloud-sync interference issue, cheap to check, expensive to keep silently absorbing.

### 2. Sanity-check the GOP pipeline on real recordings
- Record yourself (or a colleague) saying a handful of words correctly, then the same words with a deliberate, specific mispronunciation (swap `ɽ` for plain `r`, drop aspiration, etc.).
- Run each through `gop_pipeline.py` and check: do the GOP scores actually come out lower specifically at the sound you changed, not just uniformly lower everywhere?
- This is more informative than the PER number alone, since PER tells you "how often is it right" but not "does its confidence pattern make clinical sense" — and it's a cheap, fast check to do before trusting this on anything real.

---

## Near-term (next 2-4 weeks) — the actual bottleneck

Everything above is model engineering, which has been going well. The project's real bottleneck has never been the model — it's the total absence of Urdu child speech data. These two tracks should now become the priority, run in parallel with each other and with any further model tinkering:

### 3. Design the phonemically-balanced elicitation word list
- Still not done (flagged in Doc D). Every Urdu phoneme from the corrected inventory (Doc B, Section 2a) needs to appear multiple times, in multiple word positions, including the aspirated/retroflex/nasalized contrasts.
- Get this reviewed by an Urdu-speaking SLP or linguist before recording anything — this list is the foundation every subsequent data-collection step depends on, so it's worth getting right before scaling up.

### 4. Start recording typically-developing Urdu-speaking children
- No clinical access needed — just parental consent and the elicitation list from step 3.
- Target: 20-30 children minimum, spread across ages 4-12.
- Get manual phonetic transcriptions (not just orthographic) for at least a fifth of the recordings — this becomes your first real Urdu child ground-truth set and held-out evaluation data.

### 5. Start clinical/hospital outreach now, not after step 4
- This is the single longest-lead-time item in the whole project (Doc D flags this explicitly). Contacting a speech therapy clinic or hospital about eventual access to children with diagnosed speech disorders should be happening *starting today*, in parallel with everything else — not queued up to start after the typically-developing recordings are finished.
- Submit any required ethics/IRB paperwork as early as possible; approval timelines are typically the slowest single delay in projects like this.

---

## Medium-term (once child data starts arriving)

### 6. Fine-tune Backbone-v1 (or the winning backbone from step 1) on typically-developing child speech
- Expect the adult-to-child acoustic gap to hurt initially — pitch, rate, and articulation immaturity all differ meaningfully from the adult Common Voice data this model has only ever seen.
- This is also the point to revisit the augmentation techniques that were skipped during the adult-data run (Doc D's status notes flag this): VTLP specifically, since it's designed to bridge exactly this kind of vocal-tract-length gap between adult training data and child target speakers.

### 7. Validate GOP against real human judgment
- Once typically-developing child recordings with manual transcriptions exist, compute GOP scores across them and check whether low-GOP segments actually correspond to genuine mispronunciations a human transcriber flagged — not just synthetic test cases anymore.
- This is the calibration step flagged as necessary back in Section 4e of Doc C, and it's the real gate before trusting this tool on anything resembling clinical use.

### 8. Once disordered-speech data exists from clinical partnerships
- Only at this point does Phase 6 (disorder classification) become meaningful to build — per Doc A's design, start with the simplest viable model (binary typically-developing vs. disordered screening) before attempting the full multi-category classifier, since that's a far smaller data requirement and is independently useful as a first-pass tool.

---

## What NOT to do

- Don't keep iterating on adult-data model quality indefinitely. 13.21% PER (or whatever the winning backbone achieves) is a reasonable stopping point for this stage — further gains here don't address the actual bottleneck.
- Don't let any single training run go unmonitored for hours without checking in — the checkpoint-resume bug documented in Doc C, Section 2b, is a direct example of the cost of that.
- Don't skip the elicitation-list SLP review to save time — a flawed word list propagates errors into every recording made from it afterward, the same way a wrong G2P label propagated into every training example built from it (Doc B's whole debugging saga is a case study in exactly this kind of compounding cost).
