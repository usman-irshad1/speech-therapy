import os
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
MODEL_ID = "facebook/wav2vec2-xls-r-300m"
OUTPUT_DIR = r"C:\Users\usman\Desktop\spech_pipeline\urdu_xls_r_phoneme"

# UPDATED: Resume from the newly saved checkpoint-800
RESUME_CHECKPOINT = os.path.join(OUTPUT_DIR, "checkpoint-3200")  

# wav2vec2/XLS-R's CNN feature encoder downsamples raw audio by this factor
# (conv strides 5*2*2*2*2*2*2 = 320). Used to filter out examples where the
# model literally cannot produce enough output frames for the label length
# -- these are the exact examples causing eval_loss=inf.
DOWNSAMPLE_FACTOR = 320


# ---------------------------------------------------------------------
# Root-cause fix: filter out any example where the model's output frame
# count (input_length // 320) doesn't exceed the label length. This is
# the actual data problem behind eval_loss=inf -- ctc_zero_infinity below
# is a safety net, not a substitute for removing genuinely bad examples
# (which are also silently contributing zero-value/corrupted gradient
# steps during TRAINING, not just breaking eval).
# ---------------------------------------------------------------------
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
        input_features = [{"input_values": feature["input_values"]} for feature in features]
        label_features = [{"input_ids": feature["labels"]} for feature in features]

        batch = self.processor.pad(input_features, padding=self.padding, return_tensors="pt")
        labels_batch = self.processor.tokenizer.pad(label_features, padding=self.padding, return_tensors="pt")

        labels = labels_batch["input_ids"].masked_fill(labels_batch.attention_mask.ne(1), -100)
        batch["labels"] = labels
        return batch


def compute_per(pred_ids_batch, label_ids_batch, processor: Wav2Vec2Processor) -> float:
    """Phoneme Error Rate via Levenshtein distance -- gives you an actual
    interpretable metric instead of raw CTC loss, which is hard to read
    on its own (is 8.3 good? bad? no way to tell without this)."""

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

    import numpy as np
    total_per, n_examples = 0.0, 0
    for pred_ids, label_ids in zip(pred_ids_batch, label_ids_batch):
        label_ids = [i for i in label_ids if i != -100]
        pred_tokens = processor.tokenizer.convert_ids_to_tokens(np.argmax(pred_ids, axis=-1) if pred_ids.ndim > 1 else pred_ids)
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
    import numpy as np
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

    print("Initializing model...")
    model = Wav2Vec2ForCTC.from_pretrained(
        MODEL_ID,
        ctc_loss_reduction="mean",
        ctc_zero_infinity=True,   # <-- the fix: zero out any remaining
                                  # pathological example's loss instead of
                                  # letting it poison the whole batch/epoch
                                  # average. Safety net on top of the
                                  # filtering above, not a replacement for it.
        pad_token_id=processor.tokenizer.pad_token_id,
        vocab_size=len(processor.tokenizer),
    )

    model.freeze_feature_encoder()
    model.gradient_checkpointing_enable()

    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=8,
        per_device_eval_batch_size=2,
        eval_accumulation_steps=10,  # <-- NEW FIX: Flushes eval tensors to CPU memory
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
        load_best_model_at_end=True, #
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

    print("Resuming training from checkpoint-800 with fixes applied...")
    trainer.train(resume_from_checkpoint=RESUME_CHECKPOINT)

    print(f"Saving final model to {OUTPUT_DIR}...")
    trainer.save_model(OUTPUT_DIR)
    processor.save_pretrained(OUTPUT_DIR)
    print("Training complete!")