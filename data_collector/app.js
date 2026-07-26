const WORDS_LIST = [
  { id: 1, urdu: "پانی", transliteration: "Paani", meaning: "Water", target: "Nasal /n/" },
  { id: 2, urdu: "بلی", transliteration: "Billi", meaning: "Cat", target: "Geminate /lː/" },
  { id: 3, urdu: "کتا", transliteration: "Kutta", meaning: "Dog", target: "Geminate /tː/" },
  { id: 4, urdu: "گھر", transliteration: "Ghar", meaning: "House", target: "Aspirated /gʰ/" },
  { id: 5, urdu: "کھڑا", transliteration: "Khara", meaning: "Standing", target: "Aspirated /kʰ/ + Retroflex flap /ɽ/" },
  { id: 6, urdu: "بڑا", transliteration: "Bara", meaning: "Big", target: "Retroflex flap /ɽ/" },
  { id: 7, urdu: "لڑکا", transliteration: "Larka", meaning: "Boy", target: "Retroflex flap /ɽ/" },
  { id: 8, urdu: "لڑکی", transliteration: "Larki", meaning: "Girl", target: "Retroflex flap /ɽ/" },
  { id: 9, urdu: "دودھ", transliteration: "Doodh", meaning: "Milk", target: "Aspirated /dʰ/" },
  { id: 10, urdu: "پھول", transliteration: "Phool", meaning: "Flower", target: "Aspirated /pʰ/" },
  { id: 11, urdu: "مچھلی", transliteration: "Machhli", meaning: "Fish", target: "Aspirated affricate /tʃʰ/" },
  { id: 12, urdu: "چڑیا", transliteration: "Chiriya", meaning: "Bird", target: "Affricate /tʃ/ + Retroflex flap /ɽ/" },
  { id: 13, urdu: "گاؤں", transliteration: "Gaon", meaning: "Village", target: "Nasalized vowel /ں/" },
  { id: 14, urdu: "کہاں", transliteration: "Kahan", meaning: "Where", target: "Nasalized vowel /ں/" },
  { id: 15, urdu: "میں", transliteration: "Main", meaning: "I / In", target: "Nasalized vowel /ں/" },
  { id: 16, urdu: "ٹماٹر", transliteration: "Tamatar", meaning: "Tomato", target: "Retroflex stop /ʈ/" },
  { id: 17, urdu: "ڈبہ", transliteration: "Dabba", meaning: "Box", target: "Retroflex stop /ɖ/" },
  { id: 18, urdu: "ٹھنڈا", transliteration: "Thanda", meaning: "Cold", target: "Aspirated retroflex /ʈʰ/" },
  { id: 19, urdu: "ڈھول", transliteration: "Dhool", meaning: "Drum", target: "Aspirated retroflex /ɖʰ/" },
  { id: 20, urdu: "قلم", transliteration: "Qalam", meaning: "Pen", target: "Uvular stop /q/" },
  { id: 21, urdu: "خرگوش", transliteration: "Khargoosh", meaning: "Rabbit", target: "Velar fricative /x/" },
  { id: 22, urdu: "غبارہ", transliteration: "Ghubara", meaning: "Balloon", target: "Voiced fricative /ɣ/" },
  { id: 23, urdu: "جھولا", transliteration: "Jhoola", meaning: "Swing", target: "Aspirated affricate /dʒʰ/" },
  { id: 24, urdu: "جوتا", transliteration: "Joota", meaning: "Shoe", target: "Affricate /dʒ/" },
  { id: 25, urdu: "سیب", transliteration: "Seeb", meaning: "Apple", target: "Fricative /s/" },
  { id: 26, urdu: "زبان", transliteration: "Zaban", meaning: "Tongue", target: "Fricative /z/" },
  { id: 27, urdu: "شام", transliteration: "Shaam", meaning: "Evening / Lion", target: "Postalveolar /ʃ/" },
  { id: 28, urdu: "ہاتھی", transliteration: "Haathi", meaning: "Elephant", target: "Glottal /h/ + Aspirated /tʰ/" },
  { id: 29, urdu: "مکھی", transliteration: "Makkhi", meaning: "Fly", target: "Aspirated /kʰ/" },
  { id: 30, urdu: "آنکھ", transliteration: "Aankh", meaning: "Eye", target: "Velar nasal /ŋ/ + /kʰ/" },
  { id: 31, urdu: "ناک", transliteration: "Naak", meaning: "Nose", target: "Nasal /n/, /k/" },
  { id: 32, urdu: "رنگ", transliteration: "Rang", meaning: "Color", target: "Velar nasal /ŋ/" },
  { id: 33, urdu: "تتلی", transliteration: "Titli", meaning: "Butterfly", target: "Dental /t/, Liquid /l/" },
  { id: 34, urdu: "انڈا", transliteration: "Anda", meaning: "Egg", target: "Nasal /n/ + Retroflex /ɖ/" },
  { id: 35, urdu: "اونٹ", transliteration: "Oont", meaning: "Camel", target: "Retroflex stop /ʈ/" }
];

// App State
let currentIndex = 0;
let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;
let startTime = 0;
let timerInterval = null;

// Audio Visualizer Context
let audioCtx = null;
let analyser = null;
let microphoneStream = null;
let animFrameId = null;

// Recorded Blobs Map: wordId -> { blob, url, filename }
const recordingsMap = {};

// DOM Elements
const urduDisplay = document.getElementById("urduDisplay");
const transliterationDisplay = document.getElementById("transliterationDisplay");
const meaningDisplay = document.getElementById("meaningDisplay");
const targetSoundBadge = document.getElementById("targetSoundBadge");
const wordBadge = document.getElementById("wordBadge");
const progressFill = document.getElementById("progressFill");
const progressText = document.getElementById("progressText");

const btnRecord = document.getElementById("btnRecord");
const recordIcon = document.getElementById("recordIcon");
const recordLabel = document.getElementById("recordLabel");
const btnPrev = document.getElementById("btnPrev");
const btnNext = document.getElementById("btnNext");
const btnGrid = document.getElementById("btnGrid");

const childIdInput = document.getElementById("childIdInput");
const takeSelect = document.getElementById("takeSelect");

const audioPreview = document.getElementById("audioPreview");
const previewContainer = document.getElementById("previewContainer");
const timerOverlay = document.getElementById("timerOverlay");

const gridModal = document.getElementById("gridModal");
const btnCloseGrid = document.getElementById("btnCloseGrid");
const wordGrid = document.getElementById("wordGrid");
const toast = document.getElementById("toast");
const toastMessage = document.getElementById("toastMessage");

const canvas = document.getElementById("visualizer");
const canvasCtx = canvas.getContext("2d");

// Initialize App
document.addEventListener("DOMContentLoaded", () => {
  renderWord(currentIndex);
  buildWordGrid();

  // Event Listeners
  btnRecord.addEventListener("click", toggleRecording);
  btnPrev.addEventListener("click", () => navigate(-1));
  btnNext.addEventListener("click", () => navigate(1));
  btnGrid.addEventListener("click", () => openGrid(true));
  btnCloseGrid.addEventListener("click", () => openGrid(false));

  childIdInput.addEventListener("change", updateSaveDirectoryNotice);
  takeSelect.addEventListener("change", updateSaveDirectoryNotice);

  // Keybindings for rapid recording
  document.addEventListener("keydown", (e) => {
    if (e.target.tagName === "INPUT" || e.target.tagName === "SELECT") return;
    if (e.code === "Space") {
      e.preventDefault();
      toggleRecording();
    } else if (e.code === "ArrowLeft") {
      navigate(-1);
    } else if (e.code === "ArrowRight") {
      navigate(1);
    }
  });

  resizeCanvas();
  window.addEventListener("resize", resizeCanvas);
  drawIdleVisualizer();
});

function renderWord(index) {
  const word = WORDS_LIST[index];
  urduDisplay.textContent = word.urdu;
  transliterationDisplay.textContent = word.transliteration;
  meaningDisplay.textContent = word.meaning;
  targetSoundBadge.textContent = `Target: ${word.target}`;
  wordBadge.textContent = `Word ${word.id} of ${WORDS_LIST.length}`;

  const pct = Math.round(((index + 1) / WORDS_LIST.length) * 100);
  progressFill.style.width = `${pct}%`;
  progressText.textContent = `${index + 1} / ${WORDS_LIST.length} (${pct}%)`;

  btnPrev.disabled = index === 0;
  btnNext.disabled = index === WORDS_LIST.length - 1;

  // Check if recording exists
  if (recordingsMap[word.id]) {
    audioPreview.src = recordingsMap[word.id].url;
    previewContainer.style.display = "block";
  } else {
    previewContainer.style.display = "none";
    audioPreview.src = "";
  }

  updateGridActiveCard();
}

function navigate(direction) {
  if (isRecording) stopRecording();
  const nextIdx = currentIndex + direction;
  if (nextIdx >= 0 && nextIdx < WORDS_LIST.length) {
    currentIndex = nextIdx;
    renderWord(currentIndex);
  }
}

// Audio Recording Logic
async function toggleRecording() {
  if (!isRecording) {
    await startRecording();
  } else {
    stopRecording();
  }
}

async function startRecording() {
  try {
    microphoneStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    
    // Set up Web Audio API visualizer
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    analyser = audioCtx.createAnalyser();
    analyser.fftSize = 256;
    const source = audioCtx.createMediaStreamSource(microphoneStream);
    source.connect(analyser);

    // MediaRecorder
    audioChunks = [];
    let mimeType = 'audio/webm';
    if (MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
      mimeType = 'audio/webm;codecs=opus';
    } else if (MediaRecorder.isTypeSupported('audio/mp4')) {
      mimeType = 'audio/mp4';
    }

    mediaRecorder = new MediaRecorder(microphoneStream, { mimeType });
    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) audioChunks.push(e.data);
    };

    mediaRecorder.onstop = async () => {
      const audioBlob = new Blob(audioChunks, { type: mediaRecorder.mimeType });
      const audioUrl = URL.createObjectURL(audioBlob);
      const word = WORDS_LIST[currentIndex];

      recordingsMap[word.id] = {
        blob: audioBlob,
        url: audioUrl,
        filename: `${String(word.id).padStart(2, '0')}_${word.transliteration}.webm`
      };

      audioPreview.src = audioUrl;
      previewContainer.style.display = "block";
      updateGridRecordedCard(word.id);

      // Auto-Save to Laptop Server API
      await saveAudioToServer(word, audioBlob);
    };

    mediaRecorder.start();
    isRecording = true;
    btnRecord.classList.add("recording");
    recordIcon.textContent = "■";
    recordLabel.textContent = "STOP RECORDING";

    timerOverlay.style.display = "block";
    startTime = Date.now();
    timerInterval = setInterval(updateTimer, 100);

    drawActiveVisualizer();
  } catch (err) {
    showToast("Microphone access denied or unavailable!");
    console.error("Mic error:", err);
  }
}

function stopRecording() {
  if (mediaRecorder && isRecording) {
    mediaRecorder.stop();
    microphoneStream.getTracks().forEach(track => track.stop());
    isRecording = false;
    btnRecord.classList.remove("recording");
    recordIcon.textContent = "🎤";
    recordLabel.textContent = "RECORD AUDIO";

    clearInterval(timerInterval);
    timerOverlay.style.display = "none";
    if (animFrameId) cancelAnimationFrame(animFrameId);
    drawIdleVisualizer();
  }
}

function updateTimer() {
  const elapsed = (Date.now() - startTime) / 1000;
  timerOverlay.textContent = `${elapsed.toFixed(1)}s`;
}

// Save audio file directly to local server folder on Laptop
async function saveAudioToServer(word, blob) {
  const childId = childIdInput.value.trim() || "Child_001";
  const takeNo = takeSelect.value;
  const fileName = `${String(word.id).padStart(2, '0')}_${word.transliteration}.wav`;

  const formData = new FormData();
  formData.append("audio", blob, fileName);
  formData.append("child_id", childId);
  formData.append("take_no", takeNo);
  formData.append("word_id", word.id);
  formData.append("word_urdu", word.urdu);
  formData.append("transliteration", word.transliteration);

  try {
    const res = await fetch("/api/save_audio", {
      method: "POST",
      body: formData
    });
    if (res.ok) {
      const data = await res.json();
      showToast(`Saved to Laptop: ${data.saved_path || fileName}`);
    } else {
      // Server not active fallback
      triggerBrowserDownload(blob, fileName);
      showToast(`Downloaded locally: ${fileName}`);
    }
  } catch (err) {
    // If backend server not running, fallback to browser download
    triggerBrowserDownload(blob, fileName);
    showToast(`Saved recording: ${fileName}`);
  }
}

function triggerBrowserDownload(blob, fileName) {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = fileName;
  a.click();
}

// Audio Visualizer Canvas Drawing
function resizeCanvas() {
  canvas.width = canvas.parentElement.clientWidth;
  canvas.height = canvas.parentElement.clientHeight;
}

function drawIdleVisualizer() {
  canvasCtx.clearRect(0, 0, canvas.width, canvas.height);
  canvasCtx.beginPath();
  canvasCtx.moveTo(0, canvas.height / 2);
  canvasCtx.lineTo(canvas.width, canvas.height / 2);
  canvasCtx.strokeStyle = "rgba(148, 163, 184, 0.3)";
  canvasCtx.lineWidth = 2;
  canvasCtx.stroke();
}

function drawActiveVisualizer() {
  if (!isRecording || !analyser) return;

  const bufferLength = analyser.frequencyBinCount;
  const dataArray = new Uint8Array(bufferLength);
  analyser.getByteFrequencyData(dataArray);

  canvasCtx.clearRect(0, 0, canvas.width, canvas.height);
  const barWidth = (canvas.width / bufferLength) * 2.5;
  let x = 0;

  for (let i = 0; i < bufferLength; i++) {
    const barHeight = (dataArray[i] / 255) * canvas.height;
    canvasCtx.fillStyle = `rgb(99, 102, 241)`;
    canvasCtx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);
    x += barWidth + 1;
  }

  animFrameId = requestAnimationFrame(drawActiveVisualizer);
}

// Word Grid Modal & Navigation
function buildWordGrid() {
  wordGrid.innerHTML = "";
  WORDS_LIST.forEach((word, idx) => {
    const card = document.createElement("div");
    card.className = `grid-card ${idx === currentIndex ? 'active' : ''}`;
    card.id = `gridCard_${word.id}`;
    card.innerHTML = `
      <div class="grid-card-urdu">${word.urdu}</div>
      <div class="grid-card-trans">${word.id}. ${word.transliteration}</div>
    `;
    card.addEventListener("click", () => {
      currentIndex = idx;
      renderWord(currentIndex);
      openGrid(false);
    });
    wordGrid.appendChild(card);
  });
}

function updateGridActiveCard() {
  document.querySelectorAll(".grid-card").forEach((card, idx) => {
    card.classList.toggle("active", idx === currentIndex);
  });
}

function updateGridRecordedCard(wordId) {
  const card = document.getElementById(`gridCard_${wordId}`);
  if (card) card.classList.add("recorded");
}

function openGrid(isOpen) {
  gridModal.classList.toggle("open", isOpen);
}

function updateSaveDirectoryNotice() {
  const childId = childIdInput.value.trim() || "Child_001";
  const takeNo = takeSelect.value;
  console.log(`Recordings path: recordings/${childId}/Take_${takeNo}/`);
}

function showToast(msg) {
  toastMessage.textContent = msg;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 3500);
}
