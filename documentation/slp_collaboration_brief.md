# Collaboration Brief & Word-List Review for Speech-Language Pathologists (SLPs)

**Project Title**: Automatic Speech Sound Disorder (SSD) Assessment Pipeline for Urdu-Speaking Children  
**Document Purpose**: Project Introduction, Clinical Feedback Request & Elicitation Word List Review  

---

## 1. Project Background & Vision

Currently, no public Speech Sound Disorder (SSD) dataset or automated screening pipeline exists specifically for **Urdu-speaking children**. Speech-Language Pathologists (SLPs) rely heavily on manual assessment, which is time-consuming and scarce in many regions.

We are developing an **AI-assisted phoneme-level speech assessment system** designed to support SLPs. Rather than a "black-box" model, our tool uses a **two-stage, phoneme-first architecture**:

1. **Phoneme Recognition & Forced Alignment**: Uses a fine-tuned Urdu acoustic model to time-align speech to individual phonemes.
2. **Goodness-of-Pronunciation (GOP) Scoring**: Automatically measures pronunciation accuracy for every sound, flagging specific **substitutions** (e.g., swapping `/ɽ/` for `/r/`), **omissions**, and fine-grained **distortions**.
3. **Clinical Interpretability**: Generates an objective, per-phone diagnostic report (including Percentage of Consonants Correct - PCC) to assist SLPs during screening and progress tracking.

---

## 2. Why We Need Your Clinical Expertise

Machine learning models require clinical ground truth. We need your guidance to ensure our tools align with real-world Urdu clinical practice:

- **Elicitation Word-List Validation**: Reviewing our proposed 35-word picture-naming list to ensure words are familiar, age-appropriate, and phonemically balanced.
- **Developmental Baseline Guidance**: Differentiating normal age-appropriate developmental sound acquisition (e.g., late-developing sounds like `/ɽ/` in 4-year-olds) from genuine clinical speech disorders.
- **Common Error Pattern Insights**: Validating common Urdu phonological substitution patterns (e.g., loss of aspiration, retroflex flattening, denasalization).
- **Audio Sample & Transcription Review**: Spot-checking phonetic transcriptions for a small benchmark dataset of children's speech.

---

## 3. Proposed 35-Word Elicitation List for Review

This 35-word list is designed to test every key Urdu phonetic contrast—especially **aspirated plosives**, **retroflex sounds (ڑ, ٹ, ڈ)**, **nasalized vowels (ں)**, and loan sounds (`ق`, `خ`, `غ`)—using simple, concrete words suitable for picture-naming tasks with children aged 4–12.

| # | Urdu Word | Transliteration | Meaning | Target Sound(s) Exercised |
|---|---|---|---|---|
| 1 | **پانی** | Paani | Water | High-frequency baseline, dental nasal `/n/` |
| 2 | **بلی** | Billi | Cat | Geminate liquid `/lː/` |
| 3 | **کتا** | Kutta | Dog | Geminate dental `/tː/` |
| 4 | **گھر** | Ghar | House | Voiced aspirated velar `/gʰ/` |
| 5 | **کھڑا** | Khara | Standing | Voiceless aspirated velar `/kʰ/` + **Retroflex flap `/ɽ/`** |
| 6 | **بڑا** | Bara | Big | **Retroflex flap `/ɽ/`** |
| 7 | **لڑکا** | Larka | Boy | **Retroflex flap `/ɽ/`** |
| 8 | **لڑکی** | Larki | Girl | **Retroflex flap `/ɽ/`** |
| 9 | **دودھ** | Doodh | Milk | Voiced aspirated dental `/dʰ/` |
| 10 | **پھول** | Phool | Flower | Voiceless aspirated bilabial `/pʰ/` |
| 11 | **مچھلی** | Machhli | Fish | Voiceless aspirated palatal affricate `/tʃʰ/` |
| 12 | **چڑیا** | Chiriya | Bird | Palatal affricate `/tʃ/` + **Retroflex flap `/ɽ/`** |
| 13 | **گاؤں** | Gaon | Village | **Nasalized vowel `/ɑ̃/` (`ں`)** |
| 14 | **کہاں** | Kahan | Where | **Nasalized vowel `/ɑ̃/` (`ں`)** |
| 15 | **میں** | Main | I / In | **Nasalized vowel `/ẽ/` (`ں`)** |
| 16 | **ٹماٹر** | Tamatar | Tomato | Retroflex stop `/ʈ/` |
| 17 | **ڈبہ** | Dabba | Box | Retroflex stop `/ɖ/` |
| 18 | **ٹھنڈا** | Thanda | Cold | Aspirated retroflex stop `/ʈʰ/` |
| 19 | **ڈھول** | Dhool | Drum | Aspirated retroflex stop `/ɖʰ/` |
| 20 | **قلم** | Qalam | Pen | Uvular stop `/q/` |
| 21 | **خرگوش** | Khargoosh | Rabbit | Velar fricative `/x/` |
| 22 | **غبارہ** | Ghubara | Balloon | Voiced velar fricative `/ɣ/` |
| 23 | **جھولا** | Jhoola | Swing | Aspirated palatal affricate `/dʒʰ/` |
| 24 | **جوتا** | Joota | Shoe | Palatal affricate `/dʒ/` |
| 25 | **سیب** | Seeb | Apple | Alveolar fricative `/s/` |
| 26 | **زبان** | Zaban | Tongue | Alveolar fricative `/z/` |
| 27 | **شام** | Shaam | Evening / Lion | Postalveolar fricative `/ʃ/` |
| 28 | **ہاتھی** | Haathi | Elephant | Glottal `/h/` + Aspirated dental `/tʰ/` |
| 29 | **مکھی** | Makkhi | Fly (insect) | Aspirated velar `/kʰ/` |
| 30 | **آنکھ** | Aankh | Eye | Velar nasal environment `/ŋ/` + `/kʰ/` |
| 31 | **ناک** | Naak | Nose | Bilabial/dental nasal `/n/`, `/k/` |
| 32 | **رنگ** | Rang | Color | Velar nasal environment `/ŋ/` (before `/g/`) |
| 33 | **تتلی** | Titli | Butterfly | Dental stop `/t/`, Liquid `/l/` |
| 34 | **انڈا** | Anda | Egg | Nasal `/n/` + Retroflex stop `/ɖ/` |
| 35 | **اونٹ** | Oont | Camel | Retroflex stop `/ʈ/` |

---

## 4. Required Audio Sample Targets & Repetitions Per Word

To build a clinically sound dataset, we need multiple takes per word across two child cohorts:

### 1. Repetitions Per Child (3 Takes Per Word)
- **Each child should record each target word 3 separate times** (e.g., prompting the child with picture cards to say *"پانی"*, *"پانی"*, *"پانی"*).
- **Why 3 takes?** Measuring **error consistency across repeated attempts** is a vital clinical marker. Inconsistent error patterns across repeated attempts of the same word indicate **Childhood Apraxia of Speech (CAS)**, whereas consistent errors indicate a **Phonological Disorder**.

### 2. Targeted Total Samples Per Word

| Cohort Category | Target Number of Children | Repetitions Per Word | **Total Required Audio Samples Per Word** | Total Corpus Audio Clips |
|---|---|---|---|---|
| **Typically-Developing Cohort** (Ages 4–12) | 20 – 30 children | 3 takes | **60 to 90 audio samples per word** | ~2,100 – 3,150 clips |
| **Disordered / Clinical Cohort** (Referred for SSD) | 15 – 20 children | 3 takes | **45 to 60 audio samples per word** | ~1,575 – 2,100 clips |

### 3. Manual Phonetic Transcription Ground-Truth
- We request SLP manual phonetic transcription (narrow IPA annotation) for **at least 20% of recorded children** (approx. 5–6 children's full recordings = **15 to 18 manual transcriptions per word**). This serves as the clinical ground-truth test benchmark.

---

## 5. Specific Feedback Requested from the Therapist

We would deeply appreciate your feedback on the following 4 questions:

1. **Vocabulary Appropriateness**: Are all 35 words familiar, everyday words that a 4-to-8-year-old Urdu-speaking child can easily recognize from a picture prompt without hesitation? (e.g., Are words like *غبارہ* or *خرگوش* universal across Urdu dialects?)
2. **Developmental Norms**: In your clinical experience, at what typical age ranges do Urdu-speaking children master:
   - Retroflex flaps (`ڑ` / `/ɽ/`)?
   - Aspirated contrasts (`پھ`, `تھ`, `ٹھ`, `کھ`) vs. unaspirated?
   - Nasalized vowels (`ں`)?
3. **Common Clinical Substitutions**: What are the most frequent sound substitutions or distortions you encounter in Urdu pediatric cases (e.g., `/ɽ/` → `/r/`, `/ʈ/` → `/t/`, loss of aspiration `/kʰ/` → `/k/`)?
4. **Elicitation Protocol**: Do you recommend single-word picture naming (repeating target word 2–3 times) or carrier phrase prompts (e.g. *"یہ ___ ہے"*) for pediatric audio collection?

---

## 5. Contact & Collaboration

If you are interested in reviewing this word list or collaborating on clinical validation, please let us know! We can provide picture flashcard decks and demo audio alignment reports.

*Thank you for helping us build clinical-grade tools for Urdu pediatric speech therapy!*
