import os
import soundfile as sf
from datasets import load_dataset

# --- Configuration ---
DATASET_NAME = "abidanoaman/unified-urdu-speech-asr"
OUTPUT_DIR = r"C:\Users\usman\Desktop\spech_pipeline\test_batch"
MAX_SAMPLES = 10  # Number of samples to extract for testing

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Created output directory: {OUTPUT_DIR}")

    print(f"Downloading/Loading dataset '{DATASET_NAME}'...")
    
    # Load dataset from Hugging Face
    try:
        ds = load_dataset(DATASET_NAME)
    except Exception as e:
        print(f"Failed to download dataset: {e}")
        return

    # Use the test split for evaluation
    split_to_use = "test" if "test" in ds else list(ds.keys())[0]
    current_ds = ds[split_to_use]

    print(f"Extracting up to {MAX_SAMPLES} samples from the '{split_to_use}' split...")
    
    saved_count = 0
    for row in current_ds:
        if saved_count >= MAX_SAMPLES:
            break

        audio_data = row.get("audio")
        transcript = row.get("transcript", row.get("text", ""))

        if audio_data is not None and "array" in audio_data:
            audio_array = audio_data["array"]
            sample_rate = audio_data.get("sampling_rate", 16000)

            filename = f"test_sample_{saved_count + 1}.wav"
            out_path = os.path.join(OUTPUT_DIR, filename)

            # Save as 16kHz WAV format ready for your GOP pipeline
            sf.write(out_path, audio_array, sample_rate)

            print(f"✅ Saved: {filename}")
            print(f"   Transcript: {transcript}\n")
            
            saved_count += 1

    print("-" * 50)
    print(f"Successfully extracted {saved_count} test files to {OUTPUT_DIR}!")
    print("You can now test any of these files using your gop.py script.")

if __name__ == "__main__":
    main()