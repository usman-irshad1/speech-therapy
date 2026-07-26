# Doc B — Urdu Phoneme Inventory & G2P Engineering
### Urdu Child Speech-Disorder Assessment Pipeline (2 of 4)

*Second of four documents. This one covers the actual sound inventory of Urdu, the Hindi-Urdu phoneme mapping, and the full G2P (text-to-phoneme) engineering saga — every bug found and fixed while building the tool that converts written Urdu into training labels. See Doc A for the overall research design, Doc C for model training engineering, and Doc D for the project roadmap.*

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
