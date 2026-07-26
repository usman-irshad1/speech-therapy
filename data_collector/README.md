# Urdu Child Speech Data Collector Web Application

An interactive, browser-based audio collection web application built to record and organize the **35-word Urdu Speech Sound Disorder (SSD) Elicitation Corpus** from children on your laptop.

---

## 🌟 Key Features

- **Interactive 35-Word Flashcards**: Displays large Urdu script, Roman transliterations, English meanings, and target phonetic contrast badges (aspirated plosives, retroflex flap `ڑ`, nasalized vowels `ں`, Perso-Arabic loan sounds).
- **Live Microphone Audio Visualizer**: Real-time frequency waveform visualizer with timer and instant playback review.
- **Automatic Laptop File Saver**: Integrated local server automatically saves audio clips directly into `data_collector/recordings/{Child_ID}/Take_{Take_No}/{01_Paani}.webm` on your laptop!
- **Session Progress & Grid Navigation**: Interactive word grid drawer allowing therapists/parents to jump to any word, tracking completed recordings with checkmarks.
- **Keyboard Shortcuts**: Press `Spacebar` to start/stop recording, `Left Arrow` for Previous Word, `Right Arrow` for Next Word.

---

## 🚀 How to Launch & Use

### Method 1: Python Automatic Local Server (Recommended)

Run the Python server from your terminal:

```bash
python data_collector/server.py
```

Then open your browser to:
👉 **[http://localhost:8000](http://localhost:8000)**

When you record audio for a word, the web app will automatically save the file directly to your laptop at:
`data_collector/recordings/{Child_ID}/Take_1/01_Paani.webm`

---

### Method 2: Standalone Browser Mode

Simply double-click `data_collector/index.html` to open it in Google Chrome, Microsoft Edge, or Firefox. 

When you record words in standalone mode, clicking Save will prompt a direct browser download of the recording file to your `Downloads/` folder.

---

## 📂 Recording File Structure

Recordings are organized on your laptop as follows:

```
data_collector/
└── recordings/
    ├── Child_001/
    │   ├── Take_1/
    │   │   ├── 01_Paani.webm
    │   │   ├── 02_Billi.webm
    │   │   ├── ...
    │   │   └── 35_Oont.webm
    │   └── Take_2/
    └── Child_002/
```
