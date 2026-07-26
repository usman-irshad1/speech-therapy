import time
import torch
import sounddevice as sd
import soundfile as sf
import numpy as np
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor

MODEL_DIR = r"C:\Users\usman\Desktop\spech_pipeline\urdu_xls_r_phoneme"
SAMPLE_RATE = 16000
DURATION = 4  # 4 seconds is plenty for single words/short phrases

def main():
    print("Loading processor and model from disk...")
    processor = Wav2Vec2Processor.from_pretrained(MODEL_DIR)
    model = Wav2Vec2ForCTC.from_pretrained(MODEL_DIR)
    model.eval()

    # 1. Countdown to prevent initial clipping
    print("\nGet ready...")
    for i in range(3, 0, -1):
        print(f" {i}...")
        time.sleep(0.6)
    
    print("\n>>> RECORDING NOW - SPEAK CLEARLY <<<")
    
    # Record audio
    audio_data = sd.rec(int(DURATION * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype='float32')
    sd.wait()
    print("Recording finished!\n")

    audio_input = np.squeeze(audio_data)

    # 2. Audio Normalization (Boosts low mic volume)
    max_val = np.max(np.abs(audio_input))
    if max_val > 0:
        audio_input = audio_input / max_val

    # 3. Save for verification
    sf.write("latest_test.wav", audio_input, SAMPLE_RATE)

    # 4. Predict
    inputs = processor(audio_input, sampling_rate=SAMPLE_RATE, return_tensors="pt", padding=True)

    with torch.no_grad():
        logits = model(inputs.input_values).logits

    predicted_ids = torch.argmax(logits, dim=-1)
    transcription = processor.batch_decode(predicted_ids)[0]

    print("="*40)
    print("🗣️ PREDICTED PHONEMES:")
    print(transcription)
    print("="*40)

if __name__ == "__main__":
    main()