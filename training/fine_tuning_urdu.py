"""
Second backbone, testing the Hindi-Urdu phonetic-transfer hypothesis from
Sections 5-6 of the pipeline doc: initialize from a Hindi-pretrained model
(ai4bharat/indicwav2vec-hindi) instead of generic multilingual XLS-R, and
see whether the closer phonetic cluster match (Hindi/Urdu/Punjabi/Sanskrit)
actually produces a better Urdu phoneme recognizer.

IMPORTANT one-time setup: ai4bharat/indicwav2vec-hindi is a GATED repo.
Visit https://huggingface.co/ai4bharat/indicwav2vec-hindi, log in, and
accept the repo's conditions once (same as you did for Kathbath earlier).
If `hf auth login` is still active, this should just work after that.

Reuses the EXACT SAME hf_dataset/{train,dev,test} you already built --
no need to re-run prepare_dataset.py. The Urdu phoneme labels are yours
regardless of backbone, and wav2vec2-family feature extraction (simple
per-utterance normalization of raw 16kHz audio) is essentially identical
across all wav2vec2-style models.

Usage:
    python fine_tuning_train_hindi_backbone.py
"""
import os
import numpy as np
import torch
from dataclasses import dataclass
from typing import Dict, List, Union
from datasets import load_from_disk
from transformers import (
    Wav2Vec2ForCTC,
    Wav2Vec2Processor,
    Trainer,
    TrainingArguments,
)

DATASET_DIR = r"C:\Users\usman\Desktop\spech_pipeline\hf_dataset"
PROCESSOR_DIR = r"C:\Users\usman\Desktop\spech_pipeline\urdu-phoneme-processor"
MODEL_ID = "ai4bharat/indicwav2vec-hindi"

# Deliberately a DIFFERENT output dir from the XLS-R run -- keeps both
# backbones' checkpoints and results separate so they can be compared
# directly afterward (same evaluate_test_set.py works on either).
OUTPUT_DIR = r"C:\Users\usman\Desktop\spech_pipeline\urdu_indicwav2vec_hindi_phoneme"

# Same wav2vec2-family CNN front end (5*2*2*2*2*2*2 = 320 downsampling) --
# this is standard across base/large/XLS-R variants; the base/large
# difference is in the transformer layers, not the CNN feature encoder.
DOWNSAMPLE_FACTOR = 320


def filter_ctc_length(dataset, name: str):
    def is_valid(example):
        n_frames = example["input_length"] // DOWNSAMPLE_FACTOR
        return n_frames > len(example["labels"])
    before = len(dataset)
    filtered = dataset.filter(is_valid)
    after = len(filtered)
    print(f"[{name}] filtered {before - after}/{before} examples "
          f"where audio is too short for its label length")
    return filtered


@dataclass
class DataCollatorCTCWithPadding:
    processor: Wav2Vec2Processor
    padding: Union[bool, str] = True

    def __call__(self, features: List[Dict[str, Union[List[int], torch.Tensor]]]) -> Dict[str, torch.Tensor]:
        input_features = [{"input_values": f["input_values"]} for f in features]
        label_features = [{"input_ids": f["labels"]} for f in features]

        batch = self.processor.pad(input_features, padding=self.padding, return_tensors="pt")
        labels_batch = self.processor.tokenizer.pad(label_features, padding=self.padding, return_tensors="pt")

        labels = labels_batch["input_ids"].masked_fill(labels_batch.attention_mask.ne(1), -100)
        batch["labels"] = labels
        return batch


def compute_per(pred_ids_batch, label_ids_batch, processor: Wav2Vec2Processor) -> float:
    def levenshtein(ref, hyp):
        m, n = len(ref), len(hyp)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                dp[i][j] = dp[i - 1][j - 1] if ref[i - 1] == hyp[j - 1] else \
                    1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])
        return dp[m][n]

    total_per, n_examples = 0.0, 0
    for pred_ids, label_ids in zip(pred_ids_batch, label_ids_batch):
        label_ids = [i for i in label_ids if i != -100]
        pred_tokens = processor.tokenizer.convert_ids_to_tokens(
            np.argmax(pred_ids, axis=-1) if pred_ids.ndim > 1 else pred_ids)
        label_tokens = processor.tokenizer.convert_ids_to_tokens(label_ids)

        collapsed, prev = [], None
        for t in pred_tokens:
            if t != prev and t != processor.tokenizer.pad_token:
                collapsed.append(t)
            prev = t
        ref = [t for t in label_tokens if t != processor.tokenizer.pad_token]
        if len(ref) == 0:
            continue
        total_per += levenshtein(ref, collapsed) / len(ref)
        n_examples += 1
    return total_per / max(n_examples, 1)


def make_compute_metrics(processor):
    def compute_metrics(pred):
        pred_ids = np.argmax(pred.predictions, axis=-1)
        return {"per": compute_per(pred_ids, pred.label_ids, processor)}
    return compute_metrics


if __name__ == "__main__":
    print("Loading processor and datasets...")
    processor = Wav2Vec2Processor.from_pretrained(PROCESSOR_DIR)

    train_dataset = load_from_disk(os.path.join(DATASET_DIR, "train"))
    dev_dataset = load_from_disk(os.path.join(DATASET_DIR, "dev"))

    train_dataset = filter_ctc_length(train_dataset, "train")
    dev_dataset = filter_ctc_length(dev_dataset, "dev")

    data_collator = DataCollatorCTCWithPadding(processor=processor, padding=True)

    print(f"Initializing model from {MODEL_ID}...")
    print("(If this fails with a gated-repo error, visit the model page on "
          "huggingface.co, accept the conditions, and make sure `hf auth "
          "login` is active, then re-run.)")

    model = Wav2Vec2ForCTC.from_pretrained(
        MODEL_ID,
        ctc_loss_reduction="mean",
        ctc_zero_infinity=True,
        pad_token_id=processor.tokenizer.pad_token_id,
        vocab_size=len(processor.tokenizer),
        ignore_mismatched_sizes=True,  # REQUIRED here: unlike XLS-R-300M
                                       # (no head at all), this checkpoint
                                       # already has a Hindi-sized head;
                                       # this tells HF to discard it and
                                       # randomly init a new one sized to
                                       # our Urdu vocab instead of erroring
                                       # on the size mismatch.
    )

    model.freeze_feature_encoder()
    model.gradient_checkpointing_enable()

    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=8,
        per_device_eval_batch_size=2,
        eval_strategy="steps",
        num_train_epochs=10,
        save_steps=400,
        eval_steps=400,
        logging_steps=100,
        learning_rate=3e-4,
        weight_decay=0.005,
        warmup_steps=500,
        save_total_limit=2,
        fp16=True,
        dataloader_num_workers=0,
        metric_for_best_model="per",
        greater_is_better=False,
    )

    trainer = Trainer(
        model=model,
        data_collator=data_collator,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=dev_dataset,
        processing_class=processor.feature_extractor,
        compute_metrics=make_compute_metrics(processor),
    )

    print("Starting training...")
    # NOTE: True (not a hardcoded checkpoint string) -- Trainer finds the
    # actual latest checkpoint in output_dir on its own. This is the fix
    # for the exact bug that cost several hours of wasted compute on the
    # XLS-R run -- never hardcode a specific checkpoint step again.
    # On a genuinely fresh run (no checkpoints yet), this correctly starts
    # from scratch rather than erroring.
    resume = True if os.path.isdir(OUTPUT_DIR) and any(
        d.startswith("checkpoint-") for d in os.listdir(OUTPUT_DIR)
    ) else None
    trainer.train(resume_from_checkpoint=resume)

    print(f"Saving final model to {OUTPUT_DIR}...")
    trainer.save_model(OUTPUT_DIR)
    processor.save_pretrained(OUTPUT_DIR)
    print("Training complete!")