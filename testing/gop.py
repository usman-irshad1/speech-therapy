import sys
import os
import re
from pathlib import Path
import numpy as np
import torch
import torchaudio
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# --- Configuration ---
MODEL_DIR = r"C:\Users\usman\Desktop\spech_pipeline\urdu_indicwav2vec_hindi_phoneme"
if not os.path.exists(MODEL_DIR):
    MODEL_DIR = r"C:\Users\usman\Desktop\spech_pipeline\urdu_xls_r_phoneme"

# Threshold below which a phone is flagged as mispronounced.
# A threshold of 0.0 means the model's top prediction was not the expected phoneme.
GOP_FLAG_THRESHOLD = 0.0

_URDU_SCRIPT_RE = re.compile(r'[\u0600-\u06FF]')

# ---------------------------------------------------------------------
# CTC Viterbi Forced Alignment 
# ---------------------------------------------------------------------
def ctc_forced_align(log_probs: np.ndarray, label_ids: list, blank_id: int) -> list:
    """Returns the position-path per frame utilizing Viterbi decoding."""
    L = len(label_ids)
    T = log_probs.shape[0]

    z = [blank_id]
    for lab in label_ids:
        z.append(lab)
        z.append(blank_id)
    S = len(z)

    if T < S:
        raise ValueError(
            f"Audio too short: {T} frames but {S} required CTC states. "
            "Cannot force an alignment that mathematically cannot exist."
        )

    NEG_INF = -1e9
    alpha = np.full((T, S), NEG_INF)
    backptr = np.full((T, S), -1, dtype=int)

    alpha[0, 0] = log_probs[0, z[0]]
    if S > 1:
        alpha[0, 1] = log_probs[0, z[1]]

    for t in range(1, T):
        for s in range(S):
            candidates = [(alpha[t - 1, s], s)]
            if s - 1 >= 0:
                candidates.append((alpha[t - 1, s - 1], s - 1))
            if s - 2 >= 0 and z[s] != blank_id and z[s] != z[s - 2]:
                candidates.append((alpha[t - 1, s - 2], s - 2))
            
            best_score, best_s = max(candidates, key=lambda c: c[0])
            alpha[t, s] = best_score + log_probs[t, z[s]]
            backptr[t, s] = best_s

    s = S - 1 if alpha[T - 1, S - 1] >= alpha[T - 1, S - 2] else S - 2
    path = [0] * T
    path[T - 1] = s
    for t in range(T - 1, 0, -1):
        s = backptr[t, s]
        path[t - 1] = s

    return path

def group_frames_by_label(position_path: list, label_ids: list, blank_id: int) -> list:
    """Position-based grouping to separate repeated adjacent phones."""
    segments = [[] for _ in label_ids]
    for t, s in enumerate(position_path):
        if s % 2 == 1:
            segments[(s - 1) // 2].append(t)
    return segments

# ---------------------------------------------------------------------
# GOP Scoring Mathematics
# ---------------------------------------------------------------------
def gop_scores(logits: np.ndarray, frame_indices: list, expected_phone_id: int):
    """Calculates the MaxLogit and Margin for the aligned frames."""
    if not frame_indices:
        return None, None
    
    seg_logits = logits[frame_indices]
    expected_vals = seg_logits[:, expected_phone_id]

    masked = seg_logits.copy()
    masked[:, expected_phone_id] = -np.inf
    max_other = masked.max(axis=1)

    gop_max_logit = float(expected_vals.mean())
    gop_margin = float((expected_vals - max_other).mean())
    return gop_max_logit, gop_margin

def get_expected_phonemes(text_or_phonemes: str, is_raw_phonemes: bool) -> str:
    if is_raw_phonemes:
        return text_or_phonemes

    if not _URDU_SCRIPT_RE.search(text_or_phonemes):
        raise ValueError("Input lacks Urdu script. Use --raw-phonemes if passing tokens directly.")

    try:
        from g2p.urdug2p import UrduG2P
    except ImportError:
        from urdug2p import UrduG2P
    g2p = UrduG2P()
    phonemes = g2p.text_to_phonemes(text_or_phonemes)
    
    if "[UNK]" in phonemes:
        raise ValueError(f"G2P produced [UNK] for '{text_or_phonemes}'. Please fix source text.")
    
    print(f"G2P Mapping: '{text_or_phonemes}' -> '{phonemes}'\n")
    return phonemes

# ---------------------------------------------------------------------
# Core Pipeline Execution
# ---------------------------------------------------------------------
def run_gop_pipeline(audio_path: str, text_or_phonemes: str, is_raw_phonemes: bool):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Initializing model on {device.upper()}...")
    
    processor = Wav2Vec2Processor.from_pretrained(MODEL_DIR)
    model = Wav2Vec2ForCTC.from_pretrained(MODEL_DIR).to(device)
    model.eval()

    # Audio Processing
    speech, sr = torchaudio.load(audio_path)
    if sr != 16000:
        speech = torchaudio.functional.resample(speech, sr, 16000)
    speech = speech.mean(dim=0)  # Ensure mono audio

    inputs = processor(speech.numpy(), sampling_rate=16000, return_tensors="pt")
    input_values = inputs.input_values.to(device)

    # Model Inference
    with torch.no_grad():
        logits = model(input_values).logits[0].cpu()  

    log_probs = torch.log_softmax(logits, dim=-1).numpy()
    logits_np = logits.numpy()

    # Phoneme Extraction & Validation
    expected_phoneme_string = get_expected_phonemes(text_or_phonemes, is_raw_phonemes)
    expected_tokens = expected_phoneme_string.split(' ')
    expected_ids = processor.tokenizer.convert_tokens_to_ids(expected_tokens)
    blank_id = processor.tokenizer.pad_token_id

    unk_id = processor.tokenizer.unk_token_id
    if unk_id in expected_ids:
        bad = [t for t, i in zip(expected_tokens, expected_ids) if i == unk_id]
        raise ValueError(f"Unmapped tokens found: {bad}")

    n_frames = input_values.shape[-1] // 320  
    if n_frames <= len(expected_ids):
        raise ValueError("Audio is too short to mathematically align with the expected phonemes.")

    # Alignment & Scoring
    position_path = ctc_forced_align(log_probs, expected_ids, blank_id)
    segments = group_frames_by_label(position_path, expected_ids, blank_id)

    print(f"{'Phone':<8} {'Frames':<10} {'GOP MaxLogit':<14} {'GOP Margin':<12} {'Status'}")
    print("-" * 65)
    
    results = []
    for token, phone_id, frames in zip(expected_tokens, expected_ids, segments):
        gop_ml, gop_m = gop_scores(logits_np, frames, phone_id)
        
        if gop_m is None:
            flag = "NO FRAMES ALIGNED"
        else:
            flag = "⚠️ MISPRONOUNCED" if gop_m < GOP_FLAG_THRESHOLD else "✅ OK"
            
        ml_str = f"{gop_ml:.3f}" if gop_ml is not None else "n/a"
        m_str = f"{gop_m:.3f}" if gop_m is not None else "n/a"
        
        print(f"{token:<8} {len(frames):<10} {ml_str:<14} {m_str:<12} {flag}")
        
        results.append({
            "phone": token, 
            "n_frames": len(frames),
            "gop_max_logit": gop_ml, 
            "gop_margin": gop_m, 
            "flag": flag
        })

    n_flagged = sum(1 for r in results if "MISPRONOUNCED" in r["flag"])
    print("-" * 65)
    print(f"Total Flags: {n_flagged}/{len(results)} phonemes fell below the confidence threshold.\n")
    
    return results

if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--raw-phonemes"]
    is_raw = "--raw-phonemes" in sys.argv

    if len(args) != 2:
        print('Usage: python gop_pipeline.py <audio_path> "<urdu text>"')
        print('       python gop_pipeline.py <audio_path> "<phoneme string>" --raw-phonemes')
        sys.exit(1)

    run_gop_pipeline(args[0], args[1], is_raw)