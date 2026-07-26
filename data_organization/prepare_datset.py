"""
Step 3a: turn the manifest CSVs (Step 2) into a HuggingFace Dataset with
audio arrays and tokenized phoneme labels, ready for Wav2Vec2ForCTC training.

Usage:
    python prepare_dataset.py
"""
import json
import os
from datasets import Dataset, Audio
from transformers import Wav2Vec2CTCTokenizer, Wav2Vec2FeatureExtractor, Wav2Vec2Processor

MANIFEST_DIR = r"C:\Users\usman\Desktop\spech_pipeline\manifests"
VOCAB_PATH = os.path.join(MANIFEST_DIR, "urdu_phoneme_vocab.json")
PROCESSOR_SAVE_DIR = r"C:\Users\usman\Desktop\spech_pipeline\urdu-phoneme-processor"
DATASET_SAVE_DIR = r"C:\Users\usman\Desktop\spech_pipeline\hf_dataset"

MODEL_ID = "facebook/wav2vec2-xls-r-300m"


def build_processor():
    tokenizer = Wav2Vec2CTCTokenizer(
        VOCAB_PATH,
        unk_token="[UNK]",
        pad_token="[PAD]",
        word_delimiter_token="|",
    )
    # Feature extractor DOES load fine from the base checkpoint (it ships
    # preprocessor_config.json even though it has no tokenizer of its own).
    feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained(MODEL_ID)
    processor = Wav2Vec2Processor(feature_extractor=feature_extractor, tokenizer=tokenizer)
    processor.save_pretrained(PROCESSOR_SAVE_DIR)
    return processor


def load_split_as_dataset(csv_path: str) -> Dataset:
    ds = Dataset.from_csv(csv_path)
    # Cast the audio_path column to Audio() so HF lazily decodes/resamples
    # to 16kHz on access instead of loading everything into memory up front.
    ds = ds.rename_column("audio_path", "audio")
    ds = ds.cast_column("audio", Audio(sampling_rate=16_000))
    return ds


def prepare_batch(batch, processor: Wav2Vec2Processor):
    audio = batch["audio"]
    batch["input_values"] = processor(
        audio["array"], sampling_rate=audio["sampling_rate"]
    ).input_values[0]
    batch["input_length"] = len(batch["input_values"])

    # IMPORTANT: our G2P output is ALREADY correctly tokenized (one phoneme
    # or '|' per space-separated unit). Do NOT pass it through the
    # tokenizer's automatic string tokenization (processor(text).input_ids)
    # -- that was tested directly and confirmed to insert spurious extra
    # '|' tokens once a literal '|' appears anywhere in the string, which
    # silently corrupts every multi-word label. Convert known tokens to ids
    # directly instead.
    token_list = batch["phonemes"].split(' ')
    batch["labels"] = processor.tokenizer.convert_tokens_to_ids(token_list)
    return batch


if __name__ == "__main__":
    processor = build_processor()

    for split in ["train", "dev", "test"]:
        csv_path = os.path.join(MANIFEST_DIR, f"{split}_manifest.csv")
        print(f"Loading {split} from {csv_path} ...")
        ds = load_split_as_dataset(csv_path)

        ds = ds.map(
            lambda b: prepare_batch(b, processor),
            remove_columns=ds.column_names,
            num_proc=1,  # keep at 1 on Windows; multiprocessing here is
                         # frequently more trouble than it's worth on Windows
        )

        out_path = os.path.join(DATASET_SAVE_DIR, split)
        ds.save_to_disk(out_path)
        print(f"[{split}] saved {len(ds)} examples to {out_path}")