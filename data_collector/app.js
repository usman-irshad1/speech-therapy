// Official Urdu 58-Word Clinical Phonological Analysis Assessment Inventory
const WORDS_LIST = [
  {"id": 1, "urdu": "میز", "transliteration": "Meiz", "meaning": "Table / Desk", "target": "Nasal /m/, Fricative /z/", "consonant": "/m/, /z/", "position": "Initial & Final", "image": "images/01_Meiz.svg", "phonemes": ["m", "ee", "z"]},
  {"id": 2, "urdu": "بندر", "transliteration": "Bandar", "meaning": "Monkey", "target": "Nasal /m/, /n/, Stop /b/, /d/", "consonant": "/b/, /n/, /d/, /r/", "position": "Initial, Medial & Final", "image": "images/02_Bandar.svg", "phonemes": ["b", "a", "n", "d", "a", "r"]},
  {"id": 3, "urdu": "آم", "transliteration": "Aam", "meaning": "Mango", "target": "Nasal /m/", "consonant": "/m/", "position": "Final", "image": "images/03_Aam.svg", "phonemes": ["aa", "m"]},
  {"id": 4, "urdu": "برف", "transliteration": "Barf", "meaning": "Snow / Ice", "target": "Stop /b/, Fricative /f/", "consonant": "/b/, /r/, /f/", "position": "Initial & Final", "image": "images/04_Barf.svg", "phonemes": ["b", "a", "r", "f"]},
  {"id": 5, "urdu": "خربوزہ", "transliteration": "Kharbooza", "meaning": "Melon", "target": "Fricative /x/, /z/, Stop /b/", "consonant": "/x/, /b/, /z/", "position": "Initial, Medial & Final", "image": "images/05_Kharbooza.svg", "phonemes": ["kh", "a", "r", "b", "oo", "z", "a"]},
  {"id": 6, "urdu": "کتاب", "transliteration": "Kitaab", "meaning": "Book", "target": "Stop /k/, /t/, /b/", "consonant": "/k/, /t/, /b/", "position": "Initial & Final", "image": "images/06_Kitaab.svg", "phonemes": ["k", "i", "t", "aa", "b"]},
  {"id": 7, "urdu": "پہاڑ", "transliteration": "Pahaar", "meaning": "Mountain", "target": "Stop /p/, Glottal /h/, Flap /ɽ/", "consonant": "/p/, /h/, /ɽ/", "position": "Initial, Medial & Final", "image": "images/07_Pahaar.svg", "phonemes": ["p", "a", "h", "aa", "r"]},
  {"id": 8, "urdu": "ٹوپی", "transliteration": "Topi", "meaning": "Cap / Hat", "target": "Retroflex /ʈ/, Stop /p/", "consonant": "/ʈ/, /p/", "position": "Initial & Medial", "image": "images/08_Topi.svg", "phonemes": ["T", "o", "p", "ii"]},
  {"id": 9, "urdu": "سانپ", "transliteration": "Saanp", "meaning": "Snake", "target": "Fricative /s/, Nasal /n/, Stop /p/", "consonant": "/s/, /n/, /p/", "position": "Initial & Final", "image": "images/09_Saanp.svg", "phonemes": ["s", "aa", "n", "p"]},
  {"id": 10, "urdu": "ویگن", "transliteration": "Wagon", "meaning": "Van / Wagon", "target": "Glide /w/, Stop /g/, Nasal /n/", "consonant": "/w/, /g/, /n/", "position": "Initial & Final", "image": "images/10_Wagon.svg", "phonemes": ["w", "ai", "g", "a", "n"]},
  {"id": 11, "urdu": "انگور", "transliteration": "Angoor", "meaning": "Grapes", "target": "Nasal /ŋ/, Stop /g/, Trill /r/", "consonant": "/g/, /r/", "position": "Medial & Final", "image": "images/11_Angoor.svg", "phonemes": ["a", "n", "g", "oo", "r"]},
  {"id": 12, "urdu": "کوا", "transliteration": "Kowa", "meaning": "Crow", "target": "Stop /k/, Glide /w/", "consonant": "/k/, /w/", "position": "Initial & Medial", "image": "images/12_Kowa.svg", "phonemes": ["k", "o", "w", "aa"]},
  {"id": 13, "urdu": "ناک", "transliteration": "Naak", "meaning": "Nose", "target": "Nasal /n/, Stop /k/", "consonant": "/n/, /k/", "position": "Initial & Final", "image": "images/13_Naak.svg", "phonemes": ["n", "aa", "k"]},
  {"id": 14, "urdu": "زبان", "transliteration": "Zaban", "meaning": "Tongue", "target": "Fricative /z/, Stop /b/, Nasal /n/", "consonant": "/z/, /b/, /n/", "position": "Initial & Final", "image": "images/14_Zaban.svg", "phonemes": ["z", "a", "b", "aa", "n"]},
  {"id": 15, "urdu": "داغ", "transliteration": "Daagh", "meaning": "Stain / Spot", "target": "Stop /d/, Fricative /ɣ/", "consonant": "/d/, /ɣ/", "position": "Initial & Final", "image": "images/15_Daagh.svg", "phonemes": ["d", "aa", "gh"]},
  {"id": 16, "urdu": "بادشاہ", "transliteration": "Baadshah", "meaning": "King", "target": "Stop /b/, /d/, Fricative /ʃ/, Glottal /h/", "consonant": "/b/, /d/, /ʃ/, /h/", "position": "Initial, Medial & Final", "image": "images/16_Baadshah.svg", "phonemes": ["b", "aa", "d", "sh", "aa", "h"]},
  {"id": 17, "urdu": "چاند", "transliteration": "Chaand", "meaning": "Moon", "target": "Affricate /tʃ/, Nasal /n/, Stop /d/", "consonant": "/tʃ/, /n/, /d/", "position": "Initial & Final", "image": "images/17_Chaand.svg", "phonemes": ["ch", "aa", "n", "d"]},
  {"id": 18, "urdu": "بکری", "transliteration": "Bakri", "meaning": "Goat", "target": "Stop /b/, /k/, Trill /r/", "consonant": "/b/, /k/, /r/", "position": "Initial & Medial", "image": "images/18_Bakri.svg", "phonemes": ["b", "a", "k", "r", "ii"]},
  {"id": 19, "urdu": "گلاس", "transliteration": "Glaas", "meaning": "Glass", "target": "Stop /g/, Liquid /l/, Fricative /s/", "consonant": "/g/, /l/, /s/", "position": "Initial & Final", "image": "images/19_Glaas.svg", "phonemes": ["g", "l", "aa", "s"]},
  {"id": 20, "urdu": "مگرمچھ", "transliteration": "Magarmachh", "meaning": "Crocodile", "target": "Aspirated Affricate /tʃʰ/", "consonant": "/m/, /g/, /r/, /tʃʰ/", "position": "Medial & Final", "image": "images/20_Magarmachh.svg", "phonemes": ["m", "a", "g", "a", "r", "m", "a", "chh"]},
  {"id": 21, "urdu": "پتنگ", "transliteration": "Patang", "meaning": "Kite", "target": "Stop /p/, /t/, Nasal /ŋ/, Stop /g/", "consonant": "/p/, /t/, /g/", "position": "Initial & Final", "image": "images/21_Patang.svg", "phonemes": ["p", "a", "t", "a", "n", "g"]},
  {"id": 22, "urdu": "تحفہ", "transliteration": "Tuhfa", "meaning": "Gift", "target": "Stop /t/, Glottal /h/, Fricative /f/", "consonant": "/t/, /h/, /f/", "position": "Initial & Medial", "image": "images/22_Tuhfa.svg", "phonemes": ["t", "u", "h", "f", "a"]},
  {"id": 23, "urdu": "تتلی", "transliteration": "Titli", "meaning": "Butterfly", "target": "Stop /t/, Liquid /l/", "consonant": "/t/, /l/", "position": "Initial & Medial", "image": "images/23_Titli.svg", "phonemes": ["t", "i", "t", "l", "ii"]},
  {"id": 24, "urdu": "دانت", "transliteration": "Daant", "meaning": "Teeth", "target": "Stop /d/, Nasal /n/, Stop /t/", "consonant": "/d/, /t/", "position": "Initial & Final", "image": "images/24_Daant.svg", "phonemes": ["d", "aa", "n", "t"]},
  {"id": 25, "urdu": "ہاتھی", "transliteration": "Haathi", "meaning": "Elephant", "target": "Glottal /h/, Aspirated Dental /tʰ/", "consonant": "/h/, /tʰ/", "position": "Initial & Medial", "image": "images/25_Haathi.svg", "phonemes": ["h", "aa", "th", "ii"]},
  {"id": 26, "urdu": "ملاح", "transliteration": "Malaah", "meaning": "Sailor", "target": "Nasal /m/, Liquid /l/, Glottal /h/", "consonant": "/m/, /l/, /h/", "position": "Initial & Final", "image": "images/26_Malaah.svg", "phonemes": ["m", "a", "l", "aa", "h"]},
  {"id": 27, "urdu": "فوج", "transliteration": "Fauj", "meaning": "Army", "target": "Fricative /f/, Affricate /dʒ/", "consonant": "/f/, /dʒ/", "position": "Initial & Final", "image": "images/27_Fauj.svg", "phonemes": ["f", "au", "j"]},
  {"id": 28, "urdu": "سورج", "transliteration": "Sooraj", "meaning": "Sun", "target": "Fricative /s/, Trill /r/, Affricate /dʒ/", "consonant": "/s/, /r/, /dʒ/", "position": "Initial & Final", "image": "images/28_Sooraj.svg", "phonemes": ["s", "oo", "r", "a", "j"]},
  {"id": 29, "urdu": "رسی", "transliteration": "Rassi", "meaning": "Rope", "target": "Trill /r/, Fricative /s/", "consonant": "/r/, /s/", "position": "Initial & Medial", "image": "images/29_Rassi.svg", "phonemes": ["r", "a", "s", "s", "ii"]},
  {"id": 30, "urdu": "شیر", "transliteration": "Sher", "meaning": "Lion", "target": "Fricative /ʃ/, Trill /r/", "consonant": "/ʃ/, /r/", "position": "Initial & Final", "image": "images/30_Sher.svg", "phonemes": ["sh", "ee", "r"]},
  {"id": 31, "urdu": "بارش", "transliteration": "Baarish", "meaning": "Rain", "target": "Stop /b/, Trill /r/, Fricative /ʃ/", "consonant": "/b/, /r/, /ʃ/", "position": "Initial & Final", "image": "images/31_Baarish.svg", "phonemes": ["b", "aa", "r", "i", "sh"]},
  {"id": 32, "urdu": "یونیفارم", "transliteration": "Uniform", "meaning": "Uniform", "target": "Glide /j/, Nasal /n/, Fricative /f/, Trill /r/, Nasal /m/", "consonant": "/j/, /n/, /f/, /r/, /m/", "position": "Initial & Medial", "image": "images/32_Uniform.svg", "phonemes": ["y", "oo", "n", "i", "f", "aa", "r", "m"]},
  {"id": 33, "urdu": "جراب", "transliteration": "Juraab", "meaning": "Socks", "target": "Affricate /dʒ/, Trill /r/, Stop /b/", "consonant": "/dʒ/, /r/, /b/", "position": "Initial & Final", "image": "images/33_Juraab.svg", "phonemes": ["j", "u", "r", "aa", "b"]},
  {"id": 34, "urdu": "چمچہ", "transliteration": "Chamcha", "meaning": "Spoon", "target": "Affricate /tʃ/, Nasal /m/", "consonant": "/tʃ/, /m/", "position": "Initial & Medial", "image": "images/34_Chamcha.svg", "phonemes": ["ch", "a", "m", "ch", "a"]},
  {"id": 35, "urdu": "کھجور", "transliteration": "Khajoor", "meaning": "Date (fruit)", "target": "Aspirated /kʰ/, Affricate /dʒ/, Trill /r/", "consonant": "/kʰ/, /dʒ/, /r/", "position": "Initial & Final", "image": "images/35_Khajoor.svg", "phonemes": ["kh", "a", "j", "oo", "r"]},
  {"id": 36, "urdu": "چڑیا", "transliteration": "Chiriya", "meaning": "Bird", "target": "Affricate /tʃ/, Flap /ɽ/, Glide /j/", "consonant": "/tʃ/, /ɽ/, /j/", "position": "Initial & Medial", "image": "images/36_Chiriya.svg", "phonemes": ["ch", "i", "r", "i", "y", "aa"]},
  {"id": 37, "urdu": "مرچ", "transliteration": "Mirch", "meaning": "Chili", "target": "Nasal /m/, Trill /r/, Affricate /tʃ/", "consonant": "/m/, /r/, /tʃ/", "position": "Initial & Final", "image": "images/37_Mirch.svg", "phonemes": ["m", "i", "r", "ch"]},
  {"id": 38, "urdu": "غبارے", "transliteration": "Ghubare", "meaning": "Balloons", "target": "Fricative /ɣ/, Stop /b/, Trill /r/", "consonant": "/ɣ/, /b/, /r/", "position": "Initial & Medial", "image": "images/38_Ghubare.svg", "phonemes": ["gh", "u", "b", "aa", "r", "e"]},
  {"id": 39, "urdu": "مرغی", "transliteration": "Murghi", "meaning": "Hen / Chicken", "target": "Nasal /m/, Trill /r/, Fricative /ɣ/", "consonant": "/m/, /r/, /ɣ/", "position": "Initial & Medial", "image": "images/39_Murghi.svg", "phonemes": ["m", "u", "r", "gh", "ii"]},
  {"id": 40, "urdu": "ٹماٹر", "transliteration": "Tamatar", "meaning": "Tomato", "target": "Retroflex /ʈ/, Nasal /m/, Trill /r/", "consonant": "/ʈ/, /m/, /r/", "position": "Initial, Medial & Final", "image": "images/40_Tamatar.svg", "phonemes": ["T", "a", "m", "aa", "T", "a", "r"]},
  {"id": 41, "urdu": "گیٹ", "transliteration": "Gate", "meaning": "Gate", "target": "Stop /g/, Retroflex /ʈ/", "consonant": "/g/, /ʈ/", "position": "Initial & Final", "image": "images/41_Gate.svg", "phonemes": ["g", "ee", "T"]},
  {"id": 42, "urdu": "ڈبہ", "transliteration": "Dabba", "meaning": "Box", "target": "Retroflex /ɖ/, Stop /b/", "consonant": "/ɖ/, /b/", "position": "Initial & Medial", "image": "images/42_Dabba.svg", "phonemes": ["D", "a", "b", "b", "a"]},
  {"id": 43, "urdu": "جھنڈا", "transliteration": "Jhanda", "meaning": "Flag", "target": "Aspirated Affricate /dʒʰ/, Nasal /n/, Retroflex /ɖ/", "consonant": "/dʒʰ/, /n/, /ɖ/", "position": "Initial & Medial", "image": "images/43_Jhanda.svg", "phonemes": ["jh", "a", "n", "D", "aa"]},
  {"id": 44, "urdu": "کارڈ", "transliteration": "Card", "meaning": "Card", "target": "Stop /k/, Trill /r/, Retroflex /ɖ/", "consonant": "/k/, /r/, /ɖ/", "position": "Initial & Final", "image": "images/44_Card.svg", "phonemes": ["k", "aa", "r", "D"]},
  {"id": 45, "urdu": "لوٹا", "transliteration": "Lota", "meaning": "Water Pot", "target": "Liquid /l/, Retroflex /ʈ/", "consonant": "/l/, /ʈ/", "position": "Initial & Medial", "image": "images/45_Lota.svg", "phonemes": ["l", "o", "T", "aa"]},
  {"id": 46, "urdu": "پلیٹ", "transliteration": "Plate", "meaning": "Plate", "target": "Stop /p/, Liquid /l/, Retroflex /ʈ/", "consonant": "/p/, /l/, /ʈ/", "position": "Initial & Final", "image": "images/46_Plate.svg", "phonemes": ["p", "l", "ee", "T"]},
  {"id": 47, "urdu": "ڈھول", "transliteration": "Dhool", "meaning": "Drum", "target": "Aspirated Retroflex /ɖʰ/, Liquid /l/", "consonant": "/ɖʰ/, /l/", "position": "Initial & Final", "image": "images/47_Dhool.svg", "phonemes": ["Dh", "oo", "l"]},
  {"id": 48, "urdu": "پڑھ", "transliteration": "Parh", "meaning": "Read", "target": "Stop /p/, Flap /ɽ/", "consonant": "/p/, /ɽ/", "position": "Initial & Final", "image": "images/48_Parh.svg", "phonemes": ["p", "a", "r"]},
  {"id": 49, "urdu": "بھالو", "transliteration": "Bhaalo", "meaning": "Bear", "target": "Aspirated /bʰ/, Liquid /l/", "consonant": "/bʰ/, /l/", "position": "Initial & Medial", "image": "images/49_Bhaalo.svg", "phonemes": ["bh", "aa", "l", "oo"]},
  {"id": 50, "urdu": "پھول", "transliteration": "Phool", "meaning": "Flower", "target": "Aspirated /pʰ/, Liquid /l/", "consonant": "/pʰ/, /l/", "position": "Initial & Final", "image": "images/50_Phool.svg", "phonemes": ["ph", "oo", "l"]},
  {"id": 51, "urdu": "پتھر", "transliteration": "Patthar", "meaning": "Stone", "target": "Stop /p/, Aspirated /tʰ/, Trill /r/", "consonant": "/p/, /tʰ/, /r/", "position": "Initial, Medial & Final", "image": "images/51_Patthar.svg", "phonemes": ["p", "a", "t", "h", "a", "r"]},
  {"id": 52, "urdu": "ٹھیلا", "transliteration": "Theela", "meaning": "Cart", "target": "Aspirated Retroflex /ʈʰ/, Liquid /l/", "consonant": "/ʈʰ/, /l/", "position": "Initial & Medial", "image": "images/52_Theela.svg", "phonemes": ["Th", "ee", "l", "aa"]},
  {"id": 53, "urdu": "آٹھ", "transliteration": "Aath", "meaning": "Eight", "target": "Aspirated Retroflex /ʈʰ/", "consonant": "/ʈʰ/", "position": "Final", "image": "images/53_Aath.svg", "phonemes": ["aa", "Th"]},
  {"id": 54, "urdu": "آنکھ", "transliteration": "Aankh", "meaning": "Eye", "target": "Aspirated Velar /kʰ/", "consonant": "/kʰ/", "position": "Final", "image": "images/54_Aankh.svg", "phonemes": ["aa", "n", "kh"]},
  {"id": 55, "urdu": "گھوڑا", "transliteration": "Ghora", "meaning": "Horse", "target": "Aspirated Velar /gʰ/, Flap /ɽ/", "consonant": "/gʰ/, /ɽ/", "position": "Initial & Medial", "image": "images/55_Ghora.svg", "phonemes": ["gh", "o", "r", "aa"]},
  {"id": 56, "urdu": "دھواں", "transliteration": "Dhuwan", "meaning": "Smoke", "target": "Aspirated Dental /dʰ/, Glide /w/, Nasalized /ں/", "consonant": "/dʰ/, /w/, /ں/", "position": "Initial & Medial", "image": "images/56_Dhuwan.svg", "phonemes": ["dh", "u", "w", "aa", "n"]},
  {"id": 57, "urdu": "چھتری", "transliteration": "Chhatri", "meaning": "Umbrella", "target": "Aspirated Affricate /tʃʰ/, Stop /t/, Trill /r/", "consonant": "/tʃʰ/, /t/, /r/", "position": "Initial & Medial", "image": "images/57_Chhatri.svg", "phonemes": ["chh", "a", "t", "r", "ii"]},
  {"id": 58, "urdu": "مچھلی", "transliteration": "Machhli", "meaning": "Fish", "target": "Nasal /m/, Aspirated Affricate /tʃʰ/, Liquid /l/", "consonant": "/m/, /tʃʰ/, /l/", "position": "Initial, Medial & Final", "image": "images/58_Machhli.svg", "phonemes": ["m", "a", "chh", "l", "ii"]}
];

// App State
let currentIndex = 0;
let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;
let startTime = 0;
let timerInterval = null;
let isGopEnabled = true;

// Audio Visualizer Context
let audioCtx = null;
let analyser = null;
let microphoneStream = null;
let animFrameId = null;

// Child Metadata State
let childInfo = {
  id: "Child_001",
  name: "",
  age: "",
  take: "1"
};

// Recorded Blobs Map: wordId -> { blob, url, filename }
let recordingsMap = {};

// Evaluations Map: wordId -> { status: 'correct'|'incorrect', responseType: 'spontaneous'|'hinted'|'repetition', incorrectPhonemes: [], errorReasons: [], substitutedSound: '', phonologicalProcesses: [], notes: '', recorded: false }
let evaluationsMap = {};

// Filter state for grid
let activeGridFilter = "all";

// DOM Elements
const intakeModal = document.getElementById("intakeModal");
const intakeChildId = document.getElementById("intakeChildId");
const intakeChildName = document.getElementById("intakeChildName");
const intakeChildAge = document.getElementById("intakeChildAge");
const intakeTakeSelect = document.getElementById("intakeTakeSelect");

const takeCompletionModal = document.getElementById("takeCompletionModal");
const completionModalTitle = document.getElementById("completionModalTitle");
const completionModalDesc = document.getElementById("completionModalDesc");
const completionChildName = document.getElementById("completionChildName");
const completionEvaluatedCount = document.getElementById("completionEvaluatedCount");
const completionAccuracy = document.getElementById("completionAccuracy");
const completionIncorrectCount = document.getElementById("completionIncorrectCount");
const btnNextTakeModal = document.getElementById("btnNextTakeModal");
const btnExportExcelModal = document.getElementById("btnExportExcelModal");
const btnCloseCompletionModal = document.getElementById("btnCloseCompletionModal");

const hdrChildId = document.getElementById("hdrChildId");
const hdrChildName = document.getElementById("hdrChildName");
const hdrChildAge = document.getElementById("hdrChildAge");
const hdrChildTake = document.getElementById("hdrChildTake");
const progressTakeLabel = document.getElementById("progressTakeLabel");
const btnEditChild = document.getElementById("btnEditChild");
const btnExportExcel = document.getElementById("btnExportExcel");
const btnExportExcelGrid = document.getElementById("btnExportExcelGrid");

const wordImage = document.getElementById("wordImage");
const urduDisplay = document.getElementById("urduDisplay");
const transliterationDisplay = document.getElementById("transliterationDisplay");
const meaningDisplay = document.getElementById("meaningDisplay");
const targetSoundBadge = document.getElementById("targetSoundBadge");
const positionBadge = document.getElementById("positionBadge");
const wordBadge = document.getElementById("wordBadge");
const evalStatusBadge = document.getElementById("evalStatusBadge");
const progressFill = document.getElementById("progressFill");
const progressText = document.getElementById("progressText");

const btnRecord = document.getElementById("btnRecord");
const recordIcon = document.getElementById("recordIcon");
const recordLabel = document.getElementById("recordLabel");
const btnPrev = document.getElementById("btnPrev");
const btnNext = document.getElementById("btnNext");
const btnGrid = document.getElementById("btnGrid");

const audioPreview = document.getElementById("audioPreview");
const previewContainer = document.getElementById("previewContainer");
const timerOverlay = document.getElementById("timerOverlay");

// TAAPU Evaluation DOM
const pillSpontaneous = document.getElementById("pillSpontaneous");
const pillHinted = document.getElementById("pillHinted");
const pillRepetition = document.getElementById("pillRepetition");
const btnFlagIncorrect = document.getElementById("btnFlagIncorrect");

const errorAnalysisBox = document.getElementById("errorAnalysisBox");
const phonemeCheckboxesRow = document.getElementById("phonemeCheckboxesRow");
const customPhonemeInput = document.getElementById("customPhonemeInput");
const btnAddCustomPhoneme = document.getElementById("btnAddCustomPhoneme");
const substitutedSoundInput = document.getElementById("substitutedSoundInput");
const slpNotesInput = document.getElementById("slpNotesInput");

const gridModal = document.getElementById("gridModal");
const btnCloseGrid = document.getElementById("btnCloseGrid");
const wordGrid = document.getElementById("wordGrid");
const toast = document.getElementById("toast");
const toastMessage = document.getElementById("toastMessage");

const canvas = document.getElementById("visualizer");
const canvasCtx = canvas.getContext("2d");

// Initialize Application
document.addEventListener("DOMContentLoaded", () => {
  initEvaluationsMap();

  if (!childInfo.name) {
    openIntakeModal(true);
  }

  renderWord(currentIndex);
  buildWordGrid();

  // Event Listeners
  btnRecord.addEventListener("click", toggleRecording);
  btnPrev.addEventListener("click", () => navigate(-1));
  btnNext.addEventListener("click", () => navigate(1));
  btnGrid.addEventListener("click", () => openGrid(true));
  btnCloseGrid.addEventListener("click", () => openGrid(false));
  btnEditChild.addEventListener("click", () => openIntakeModal(true));
  btnExportExcel.addEventListener("click", exportExcelReport);
  btnExportExcelGrid.addEventListener("click", exportExcelReport);
  btnExportExcelModal.addEventListener("click", exportExcelReport);
  btnCloseCompletionModal.addEventListener("click", () => takeCompletionModal.classList.remove("open"));

  // Response Type radio listener (Always Shown)
  document.querySelectorAll('input[name="responseType"]').forEach(r => {
    r.addEventListener("change", (e) => {
      setResponseType(e.target.value);
    });
  });

  // Flag Incorrect toggle button
  btnFlagIncorrect.addEventListener("click", toggleIncorrectStatus);

  // Substituted sound input listener
  substitutedSoundInput.addEventListener("input", (e) => {
    const word = WORDS_LIST[currentIndex];
    evaluationsMap[word.id].substitutedSound = e.target.value;
    saveEvaluationToServer();
  });

  // Error Reasons checkboxes
  document.querySelectorAll('.error-reason-pills input[type="checkbox"]').forEach(cb => {
    cb.addEventListener("change", updateErrorReasons);
  });

  // Phonological Processes checkboxes
  document.querySelectorAll('.phono-process-grid input[type="checkbox"]').forEach(cb => {
    cb.addEventListener("change", updatePhonologicalProcesses);
  });

  slpNotesInput.addEventListener("input", updateSlpNotes);
  btnAddCustomPhoneme.addEventListener("click", handleAddCustomPhoneme);

  // Grid filter tabs
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", (e) => {
      document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
      e.target.classList.add("active");
      activeGridFilter = e.target.getAttribute("data-filter");
      renderFilteredGrid();
    });
  });

  // Keybindings for rapid evaluation
  document.addEventListener("keydown", (e) => {
    if (["INPUT", "TEXTAREA", "SELECT"].includes(e.target.tagName)) return;
    if (e.code === "Space") {
      e.preventDefault();
      toggleRecording();
    } else if (e.code === "ArrowLeft") {
      navigate(-1);
    } else if (e.code === "ArrowRight") {
      navigate(1);
    } else if (e.key === "i" || e.key === "I") {
      toggleIncorrectStatus();
    }
  });

  resizeCanvas();
  window.addEventListener("resize", resizeCanvas);
  drawIdleVisualizer();
});

function initEvaluationsMap() {
  evaluationsMap = {};
  recordingsMap = {};
  WORDS_LIST.forEach(w => {
    evaluationsMap[w.id] = {
      word_id: w.id,
      urdu: w.urdu,
      transliteration: w.transliteration,
      meaning: w.meaning,
      target: w.target,
      consonant: w.consonant,
      position: w.position,
      recorded: false,
      status: "correct", // Default clean/correct unless flagged incorrect
      responseType: "spontaneous", // spontaneous, hinted, repetition
      incorrectPhonemes: [],
      errorReasons: [],
      substitutedSound: "",
      phonologicalProcesses: [],
      notes: "",
      gopFlag: "",
      audioFile: ""
    };
  });
}

// Intake Modal & Child Session Init
function openIntakeModal(isOpen) {
  intakeModal.classList.toggle("open", isOpen);
}

function startChildSession() {
  childInfo.id = intakeChildId.value.trim() || "Child_001";
  childInfo.name = intakeChildName.value.trim() || "Anonymous Child";
  childInfo.age = intakeChildAge.value.trim() || "N/A";
  childInfo.take = intakeTakeSelect.value;

  // Update Header UI
  hdrChildId.textContent = childInfo.id;
  hdrChildName.textContent = childInfo.name;
  hdrChildAge.textContent = childInfo.age;
  hdrChildTake.textContent = childInfo.take;
  progressTakeLabel.textContent = `Take ${childInfo.take}`;

  openIntakeModal(false);
  showToast(`Session Initialized: ${childInfo.name} (${childInfo.id}) — Take ${childInfo.take}`);
  saveEvaluationToServer();
}

// Render Word Flashcard & TAAPU Clinical Controls
function renderWord(index) {
  const word = WORDS_LIST[index];
  const evalData = evaluationsMap[word.id];

  wordImage.src = word.image;
  wordImage.alt = `${word.transliteration} Picture`;
  urduDisplay.textContent = word.urdu;
  transliterationDisplay.textContent = word.transliteration;
  meaningDisplay.textContent = word.meaning;
  targetSoundBadge.textContent = `Consonant: ${word.consonant}`;
  positionBadge.textContent = `Position: ${word.position}`;
  wordBadge.textContent = `Word ${word.id} of ${WORDS_LIST.length}`;

  btnPrev.disabled = index === 0;
  btnNext.disabled = index === WORDS_LIST.length - 1;

  // Audio Preview check
  if (recordingsMap[word.id]) {
    audioPreview.src = recordingsMap[word.id].url;
    previewContainer.style.display = "block";
  } else {
    previewContainer.style.display = "none";
    audioPreview.src = "";
  }

  // Render TAAPU Evaluation Panel
  renderTaapuPanel(word, evalData);
  updateOverallProgress();
  updateGridActiveCard();
}

function renderTaapuPanel(word, evalData) {
  // 1. Sync Response Type (Always Shown)
  const currentResp = evalData.responseType || "spontaneous";
  document.querySelectorAll('input[name="responseType"]').forEach(r => {
    r.checked = (r.value === currentResp);
    r.parentElement.classList.toggle("active", r.value === currentResp);
  });

  // 2. Status Pill & Error Flag Button State
  const isIncorrect = evalData.status === "incorrect";
  btnFlagIncorrect.classList.toggle("active", isIncorrect);
  btnFlagIncorrect.textContent = isIncorrect
    ? "⚠️ Mispronunciation Flagged (Click to Mark Correct)"
    : "⚠️ Mark Pronunciation Incorrect / Error";

  evalStatusBadge.className = `eval-status-pill ${isIncorrect ? 'status-incorrect' : 'status-correct'}`;
  evalStatusBadge.textContent = isIncorrect
    ? `✗ Incorrect (${evalData.incorrectPhonemes.length || 1} error/s)`
    : "✓ Pronunciation Correct";

  // 3. Show/Hide Error Analysis Box
  if (isIncorrect) {
    errorAnalysisBox.style.display = "flex";
    renderPhonemeCheckboxes(word, evalData);
    syncErrorReasons(evalData);
    syncPhonologicalProcesses(evalData);
    substitutedSoundInput.value = evalData.substitutedSound || "";
  } else {
    errorAnalysisBox.style.display = "none";
  }

  // 4. Sync Clinician Notes
  slpNotesInput.value = evalData.notes || "";
}

function setResponseType(type) {
  const word = WORDS_LIST[currentIndex];
  evaluationsMap[word.id].responseType = type;

  document.querySelectorAll('.resp-pill').forEach(pill => {
    const radio = pill.querySelector('input');
    pill.classList.toggle("active", radio.value === type);
  });

  saveEvaluationToServer();
}

function toggleIncorrectStatus() {
  const word = WORDS_LIST[currentIndex];
  const evalData = evaluationsMap[word.id];

  if (evalData.status === "correct") {
    evalData.status = "incorrect";
    if (evalData.incorrectPhonemes.length === 0 && word.phonemes.length > 0) {
      evalData.incorrectPhonemes.push(word.phonemes[0]);
    }
    showToast(`Flagged error for "${word.transliteration}"`);
  } else {
    evalData.status = "correct";
    evalData.incorrectPhonemes = [];
    evalData.errorReasons = [];
    evalData.substitutedSound = "";
    evalData.phonologicalProcesses = [];
    showToast(`Marked "${word.transliteration}" as Correct`);
  }

  renderWord(currentIndex);
  renderFilteredGrid();
  saveEvaluationToServer();
  checkTakeCompletion();
}

function renderPhonemeCheckboxes(word, evalData) {
  phonemeCheckboxesRow.innerHTML = "";

  const allPhonemes = Array.from(new Set([...word.phonemes, ...evalData.incorrectPhonemes]));

  allPhonemes.forEach(ph => {
    const label = document.createElement("label");
    label.className = "phoneme-chip-checkbox";
    
    const isChecked = evalData.incorrectPhonemes.includes(ph);
    label.innerHTML = `
      <input type="checkbox" value="${ph}" ${isChecked ? 'checked' : ''} />
      <span>/${ph}/</span>
    `;

    const checkbox = label.querySelector("input");
    checkbox.addEventListener("change", (e) => {
      togglePhonemeSelection(ph, e.target.checked);
    });

    phonemeCheckboxesRow.appendChild(label);
  });
}

function togglePhonemeSelection(phoneme, isSelected) {
  const word = WORDS_LIST[currentIndex];
  const evalData = evaluationsMap[word.id];

  if (isSelected) {
    if (!evalData.incorrectPhonemes.includes(phoneme)) {
      evalData.incorrectPhonemes.push(phoneme);
    }
  } else {
    evalData.incorrectPhonemes = evalData.incorrectPhonemes.filter(p => p !== phoneme);
  }

  renderWord(currentIndex);
  renderFilteredGrid();
  saveEvaluationToServer();
}

function updateErrorReasons() {
  const word = WORDS_LIST[currentIndex];
  const evalData = evaluationsMap[word.id];

  evalData.errorReasons = [];
  document.querySelectorAll('.error-reason-pills input[type="checkbox"]:checked').forEach(cb => {
    evalData.errorReasons.push(cb.value);
  });

  saveEvaluationToServer();
}

function syncErrorReasons(evalData) {
  document.querySelectorAll('.error-reason-pills input[type="checkbox"]').forEach(cb => {
    cb.checked = evalData.errorReasons.includes(cb.value);
  });
}

function updatePhonologicalProcesses() {
  const word = WORDS_LIST[currentIndex];
  const evalData = evaluationsMap[word.id];

  evalData.phonologicalProcesses = [];
  document.querySelectorAll('.phono-process-grid input[type="checkbox"]:checked').forEach(cb => {
    evalData.phonologicalProcesses.push(cb.value);
  });

  saveEvaluationToServer();
}

function syncPhonologicalProcesses(evalData) {
  document.querySelectorAll('.phono-process-grid input[type="checkbox"]').forEach(cb => {
    cb.checked = evalData.phonologicalProcesses.includes(cb.value);
  });
}

function handleAddCustomPhoneme() {
  const val = customPhonemeInput.value.trim().replace(/^\/+|\/+$/g, '');
  if (!val) return;

  const word = WORDS_LIST[currentIndex];
  const evalData = evaluationsMap[word.id];

  if (!evalData.incorrectPhonemes.includes(val)) {
    evalData.incorrectPhonemes.push(val);
  }
  customPhonemeInput.value = "";
  renderWord(currentIndex);
  renderFilteredGrid();
  saveEvaluationToServer();
}

function updateSlpNotes(e) {
  const word = WORDS_LIST[currentIndex];
  evaluationsMap[word.id].notes = e.target.value;
}

function updateOverallProgress() {
  const total = WORDS_LIST.length;
  const recordedCount = Object.values(evaluationsMap).filter(e => e.recorded).length;
  const pct = Math.round((recordedCount / total) * 100);

  progressFill.style.width = `${pct}%`;
  progressText.textContent = `${recordedCount} / ${total} Recorded (${pct}%)`;
}

function checkTakeCompletion() {
  const total = WORDS_LIST.length;
  const recordedCount = Object.values(evaluationsMap).filter(e => e.recorded).length;

  if (recordedCount === total) {
    showTakeCompletionModal();
  }
}

function showTakeCompletionModal() {
  const currentTake = parseInt(childInfo.take);
  const total = WORDS_LIST.length;
  const correctCount = Object.values(evaluationsMap).filter(e => e.status === "correct").length;
  const incorrectCount = Object.values(evaluationsMap).filter(e => e.status === "incorrect").length;
  const accuracy = Math.round((correctCount / total) * 100);

  completionChildName.textContent = childInfo.name;
  completionModalTitle.textContent = `Take ${currentTake} Completed!`;
  completionModalDesc.textContent = `You have completed all 35 words for Take ${currentTake} of ${childInfo.name}. Saved to folder: recordings/${childInfo.id}/take ${currentTake}`;

  completionEvaluatedCount.textContent = `${total} / ${total}`;
  completionAccuracy.textContent = `${accuracy}%`;
  completionIncorrectCount.textContent = incorrectCount;

  if (currentTake < 3) {
    const nextTake = currentTake + 1;
    btnNextTakeModal.textContent = `➡️ Proceed to Take ${nextTake}`;
    btnNextTakeModal.onclick = () => proceedToNextTake(nextTake);
  } else {
    btnNextTakeModal.textContent = `🏆 All 3 Takes Completed! (New Child)`;
    btnNextTakeModal.onclick = () => {
      takeCompletionModal.classList.remove("open");
      openIntakeModal(true);
    };
  }

  takeCompletionModal.classList.add("open");
}

function proceedToNextTake(nextTakeNo) {
  childInfo.take = String(nextTakeNo);
  hdrChildTake.textContent = childInfo.take;
  progressTakeLabel.textContent = `Take ${childInfo.take}`;
  intakeTakeSelect.value = childInfo.take;

  initEvaluationsMap();
  takeCompletionModal.classList.remove("open");

  currentIndex = 0;
  renderWord(currentIndex);
  renderFilteredGrid();
  saveEvaluationToServer();

  showToast(`🚀 Switched to Take ${childInfo.take} for ${childInfo.name}!`);
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
    
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    analyser = audioCtx.createAnalyser();
    analyser.fftSize = 256;
    const source = audioCtx.createMediaStreamSource(microphoneStream);
    source.connect(analyser);

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

      evaluationsMap[word.id].recorded = true;
      evaluationsMap[word.id].audioFile = recordingsMap[word.id].filename;

      audioPreview.src = audioUrl;
      previewContainer.style.display = "block";

      await saveAudioToServer(word, audioBlob);
      renderFilteredGrid();
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
    showToast("Microphone access denied!");
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
    recordLabel.textContent = "CLICK OR PRESS SPACEBAR TO RECORD";

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

// Server API Syncing & Excel Generation
async function saveAudioToServer(word, blob) {
  const fileName = `${String(word.id).padStart(2, '0')}_${word.transliteration}.webm`;

  const formData = new FormData();
  formData.append("audio", blob, fileName);
  formData.append("child_id", childInfo.id);
  formData.append("take_no", childInfo.take);
  formData.append("word_id", word.id);
  formData.append("word_urdu", word.urdu);
  formData.append("transliteration", word.transliteration);
  formData.append("enable_gop", isGopEnabled ? "true" : "false");

  try {
    const res = await fetch("/api/save_audio", {
      method: "POST",
      body: formData
    });
    if (res.ok) {
      const data = await res.json();
      if (data.gop_results) {
        evaluationsMap[word.id].gop_results = data.gop_results;
        const inc = data.gop_results.incorrect_phonemes || [];
        evaluationsMap[word.id].gopFlag = inc.length > 0 ? `⚠️ Mispronounced (${inc.join(", ")})` : `✅ Clean`;
      }
      showToast(`Saved to take ${childInfo.take}: ${fileName}`);
      saveEvaluationToServer();
    }
  } catch (err) {
    showToast(`Audio recorded locally: ${fileName}`);
  }
}

async function saveEvaluationToServer() {
  try {
    const payload = {
      child_info: childInfo,
      evaluations: evaluationsMap,
      timestamp: new Date().toISOString()
    };

    const res = await fetch("/api/save_evaluation", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      const data = await res.json();
      console.log("Evaluation & Excel synced on server:", data);
    }
  } catch (err) {
    console.warn("Server evaluation sync warning:", err);
  }
}

async function exportExcelReport() {
  showToast("Generating TAAPU Excel Report (.xlsx)...");
  await saveEvaluationToServer();

  const downloadUrl = `/api/download_excel?child_id=${encodeURIComponent(childInfo.id)}&take=${childInfo.take}`;

  try {
    const res = await fetch(downloadUrl);
    if (res.ok) {
      const blob = await res.blob();
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `Session_${childInfo.id}_take_${childInfo.take}.xlsx`;
      a.click();
      showToast(`Excel downloaded: Session_${childInfo.id}_take_${childInfo.take}.xlsx`);
    } else {
      generateClientSideCsvFallback();
    }
  } catch (err) {
    generateClientSideCsvFallback();
  }
}

function generateClientSideCsvFallback() {
  let csv = "Word ID,Urdu Word,Transliteration,English Meaning,Target Consonant,Phonetic Position,Response Type,Audio Recorded,Pronunciation Status,Incorrect Phonemes,Error Reason,Substituted Sound,Phonological Processes,Notes\n";
  WORDS_LIST.forEach(w => {
    const e = evaluationsMap[w.id];
    const incStr = (e.incorrectPhonemes || []).join("; ");
    const errStr = (e.errorReasons || []).join("; ");
    const procStr = (e.phonologicalProcesses || []).join("; ");
    csv += `"${w.id}","${w.urdu}","${w.transliteration}","${w.meaning}","${w.consonant}","${w.position}","${e.responseType}","${e.recorded ? 'Yes' : 'No'}","${e.status}","${incStr}","${errStr}","${e.substitutedSound}","${procStr}","${e.notes}"\n`;
  });

  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `Session_${childInfo.id}_take_${childInfo.take}.csv`;
  a.click();
  showToast(`CSV Backup downloaded!`);
}

// Visual Canvas Drawing
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
    canvasCtx.fillStyle = `rgb(59, 130, 246)`;
    canvasCtx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);
    x += barWidth + 1;
  }

  animFrameId = requestAnimationFrame(drawActiveVisualizer);
}

// Word Grid Modal & Navigation
function buildWordGrid() {
  renderFilteredGrid();
}

function renderFilteredGrid() {
  wordGrid.innerHTML = "";

  WORDS_LIST.forEach((word, idx) => {
    const evalData = evaluationsMap[word.id];

    // Filter logic
    if (activeGridFilter === "recorded" && !evalData.recorded) return;
    if (activeGridFilter === "correct" && evalData.status !== "correct") return;
    if (activeGridFilter === "incorrect" && evalData.status !== "incorrect") return;

    const card = document.createElement("div");
    card.className = `grid-card ${idx === currentIndex ? 'active' : ''}`;
    card.id = `gridCard_${word.id}`;

    let statusChip = '<span class="grid-chip chip-ok">✓ Correct</span>';
    if (evalData.status === "incorrect") {
      statusChip = `<span class="grid-chip chip-err">✗ Incorrect (${evalData.incorrectPhonemes.length || 1})</span>`;
    }

    const recChip = evalData.recorded ? '<span class="grid-chip chip-rec">🎤 Rec</span>' : '';

    card.innerHTML = `
      <img src="${word.image}" alt="${word.transliteration}" class="grid-card-img" />
      <div class="grid-card-urdu">${word.urdu}</div>
      <div class="grid-card-trans">${word.id}. ${word.transliteration}</div>
      <div class="grid-pos-tag">${word.position.split(' ')[0]}</div>
      <div class="grid-badges-row">
        ${recChip}
        ${statusChip}
      </div>
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
  document.querySelectorAll(".grid-card").forEach((card) => {
    card.classList.remove("active");
  });
  const activeCard = document.getElementById(`gridCard_${WORDS_LIST[currentIndex].id}`);
  if (activeCard) activeCard.classList.add("active");
}

function openGrid(isOpen) {
  gridModal.classList.toggle("open", isOpen);
  if (isOpen) renderFilteredGrid();
}

function showToast(msg) {
  toastMessage.textContent = msg;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 3500);
}

// Toggle ML GOP Analysis Button Handler
document.addEventListener("DOMContentLoaded", () => {
  const btnToggleGop = document.getElementById("btnToggleGop");
  if (btnToggleGop) {
    btnToggleGop.addEventListener("click", () => {
      isGopEnabled = !isGopEnabled;
      btnToggleGop.className = `btn ${isGopEnabled ? 'btn-gop-on' : 'btn-gop-off'}`;
      btnToggleGop.textContent = isGopEnabled ? "🤖 ML Feedback: ON" : "🤖 ML Feedback: OFF";
      showToast(isGopEnabled ? "🤖 Real-Time ML Feedback Enabled" : "🤖 Real-Time ML Feedback Disabled (Manual Mode)");
    });
  }
});
