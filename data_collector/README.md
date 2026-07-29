# Urdu Child Speech Data Collector Web Application

An interactive, browser-based audio collection & speech therapy assessment web application built to record, evaluate, and organize the **35-word Urdu Speech Sound Disorder (SSD) Elicitation Corpus** from children.

---

## 🌟 Key Features

- **Child Intake Form**: Mandatory initial setup screen requesting Child Name, Age, ID, and Session Take before starting data collection.
- **Word Illustration Pictures**: Every single word in the 35-word corpus features a dedicated visual SVG image vector card for clear elicitation with children.
- **Interactive SLP Pronunciation Evaluation**:
  - Speech-Language Pathologist (SLP) check buttons for **Correct (✓)** vs **Incorrect (✗)** pronunciation.
  - Interactive phoneme checkboxes listing expected phonemes for each word to easily flag which exact phoneme(s) were mispronounced.
  - Custom phoneme input for recording phonetic substitutions or distortions.
  - Clinician Notes field for qualitative commentary.
- **Automated Excel (.xlsx) Export**:
  - Automatically builds and exports a formatted Excel spreadsheet (`Session_{Child_ID}_Take_1.xlsx`).
  - **Sheet 1**: Session Summary & Child Profile (Name, Age, ID, Date, Evaluated Words, Accuracy %).
  - **Sheet 2**: Word-by-Word Assessment (Urdu, Transliteration, Target Sound, Audio Saved, Pronunciation Status, Mispronounced Phonemes, SLP Notes).
- **Interactive 35-Word Visual Grid**: Comprehensive grid displaying picture thumbnails, recording status badges, and evaluation status flags with filter tabs (`All`, `Recorded`, `Correct`, `Incorrect`, `Pending`).
- **Live Waveform Visualizer & Recording**: Real-time microphone audio visualizer with instant review player.
- **Keyboard Shortcuts**:
  - `Spacebar`: Start / Stop Recording
  - `Left / Right Arrow`: Navigate previous/next word
  - `C`: Mark Correct
  - `I`: Mark Incorrect

---

## 🚀 How to Launch & Use

### Method 1: Python Server (Recommended with Excel Export)

Run the Python server from your terminal:

```bash
python data_collector/server.py
```

Then open your browser to:
👉 **[http://localhost:8000](http://localhost:8000)**

---

## 📂 Output File Structure

Recordings and Excel reports are organized as follows:

```
data_collector/
├── images/                             # 35 Word SVG Graphic Illustrations
│   ├── 01_Paani.svg
│   ├── 02_Billi.svg
│   └── ...
└── recordings/
    └── Child_001/
        └── Take_1/
            ├── 01_Paani.webm
            ├── 02_Billi.webm
            ├── ...
            ├── Session_Child_001_Take_1.xlsx     # Formatted Excel Assessment File
            └── session_evaluations.json          # JSON Evaluation Data
```
