"""
Step 3a: turn the manifest CSVs (Step 2) into a HuggingFace Dataset with
audio arrays and tokenized phoneme labels, ready for Wav2Vec2ForCTC training.

Usage:
    python train.py
"""
import os
import librosa
import pandas as pd
from datasets import Dataset
from transformers import Wav2Vec2CTCTokenizer, Wav2Vec2FeatureExtractor, Wav2Vec2Processor

MANIFEST_DIR = r"C:\Users\usman\Desktop\spech_pipeline\manifests"
VOCAB_PATH = os.path.join(MANIFEST_DIR, "urdu_phoneme_vocab.json")
DATASET_SAVE_DIR = r"C:\Users\usman\Desktop\spech_pipeline\hf_dataset"
MODEL_ID = "facebook/wav2vec2-xls-r-300m"

# 1. Initialize the processor
tokenizer = Wav2Vec2CTCTokenizer(
    VOCAB_PATH,
    unk_token="[UNK]", 
    pad_token="[PAD]", 
    word_delimiter_token="|",
)
feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained(MODEL_ID)
processor = Wav2Vec2Processor(feature_extractor=feature_extractor, tokenizer=tokenizer)


def load_split_as_dataset(csv_path: str) -> Dataset:
    # Read CSV using headers since your files have 'audio_path,sentence,phonemes,n_unk' at the top
    df = pd.read_csv(csv_path, dtype=str)
    
    initial_count = len(df)
    
    # Replace empty strings or whitespace-only strings with NaN, then drop rows with any NaNs
    df = df.replace(r'^\s*$', float('nan'), regex=True)
    df = df.dropna().reset_index(drop=True)
    
    dropped_count = initial_count - len(df)
    if dropped_count > 0:
        print(f"  [Warning] Dropped {dropped_count} rows with missing or empty values (kept {len(df)}/{initial_count}).")
    
    # Convert dataframe to a Hugging Face dataset from dict
    ds = Dataset.from_dict({col: df[col].tolist() for col in df.columns})
    return ds


def prepare_batch(batch, processor: Wav2Vec2Processor):
    # Safely pull the absolute file path from the audio_path column
    audio_path = batch["audio_path"]
    
    # Manually load and resample audio using librosa
    speech_array, sampling_rate = librosa.load(audio_path, sr=16_000)

    batch["input_values"] = processor(
        speech_array, sampling_rate=sampling_rate
    ).input_values[0]
    batch["input_length"] = len(batch["input_values"])

    # Tokenize phonemes directly
    token_list = batch["phonemes"].split(' ')
    batch["labels"] = processor.tokenizer.convert_tokens_to_ids(token_list)
    return batch


if __name__ == "__main__":
    for split in ["train", "dev", "test"]:
        csv_path = os.path.join(MANIFEST_DIR, f"{split}_manifest.csv")
        
        if not os.path.exists(csv_path):
            print(f"Skipping {split}, file not found: {csv_path}")
            continue
            
        print(f"Loading {split} from {csv_path} ...")
        ds = load_split_as_dataset(csv_path)

        # Map dataset using librosa-based audio loading
        ds = ds.map(
            prepare_batch,
            fn_kwargs={"processor": processor},
            remove_columns=ds.column_names,
            num_proc=1,  # Keep at 1 on Windows to avoid multiprocessing issues
        )

        out_path = os.path.join(DATASET_SAVE_DIR, split)
        ds.save_to_disk(out_path)
        print(f"[{split}] saved {len(ds)} examples to {out_path}")