"""
Final, honest evaluation on the held-out test set (never touched during
training or the dev-set eval loop) -- this is the number to actually trust
and report as Backbone-v1's real performance.

Usage:
    python evaluate_test_set.py
"""
import os
import numpy as np
import torch
from datasets import load_from_disk
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor

DATASET_DIR = r"C:\Users\usman\Desktop\spech_pipeline\hf_dataset"
MODEL_DIR = r"C:\Users\usman\Desktop\spech_pipeline\urdu_indicwav2vec_hindi_phoneme"

# Same downsample factor and filter used for train/dev during training --
# applying it here too, since the worst-utterance pattern (long references
# collapsing to a handful of mostly-/ɑ/ predictions) is the exact signature
# of audio that's too short (post-downsampling) to physically fit its
# label length via CTC. Omitting this filter here was an oversight in the
# original version of this script.
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


def decode_greedy(logits_row, processor):
    pred_ids = np.argmax(logits_row, axis=-1)
    pred_tokens = processor.tokenizer.convert_ids_to_tokens(pred_ids)
    collapsed, prev = [], None
    for t in pred_tokens:
        if t != prev and t != processor.tokenizer.pad_token:
            collapsed.append(t)
        prev = t
    return collapsed


if __name__ == "__main__":
    print("Loading model and processor...")
    processor = Wav2Vec2Processor.from_pretrained(MODEL_DIR)
    model = Wav2Vec2ForCTC.from_pretrained(MODEL_DIR)
    model.eval()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)

    print("Loading held-out test set...")
    test_dataset = load_from_disk(os.path.join(DATASET_DIR, "test"))
    test_dataset = filter_ctc_length(test_dataset, "test")
    print(f"Evaluating on {len(test_dataset)} held-out examples...")

    total_per = 0.0
    n_examples = 0
    per_utterance_results = []

    with torch.no_grad():
        for i, example in enumerate(test_dataset):
            input_values = torch.tensor(example["input_values"]).unsqueeze(0).to(device)
            logits = model(input_values).logits[0].cpu().numpy()

            hyp_tokens = decode_greedy(logits, processor)
            ref_ids = [tid for tid in example["labels"] if tid != -100]
            ref_tokens = processor.tokenizer.convert_ids_to_tokens(ref_ids)
            ref_tokens = [t for t in ref_tokens if t != processor.tokenizer.pad_token]

            if len(ref_tokens) == 0:
                continue

            dist = levenshtein(ref_tokens, hyp_tokens)
            per = dist / len(ref_tokens)
            total_per += per
            n_examples += 1
            per_utterance_results.append({
                "index": i, "ref": " ".join(ref_tokens),
                "hyp": " ".join(hyp_tokens), "per": per,
            })

            if (i + 1) % 200 == 0:
                print(f"  ...{i + 1}/{len(test_dataset)} processed, "
                      f"running average PER so far: {total_per / n_examples:.4f}")

    final_per = total_per / max(n_examples, 1)
    print(f"\n=== FINAL HELD-OUT TEST SET PER: {final_per:.4f} ({final_per*100:.2f}%) ===")
    print(f"Evaluated on {n_examples} utterances (never used in training or eval-loop decisions).")

    # Show the worst 10 utterances -- useful for spotting systematic problem
    # patterns (a specific phoneme always wrong, a specific word type, etc.)
    worst = sorted(per_utterance_results, key=lambda r: -r["per"])[:10]
    print("\n--- 10 worst-performing utterances (for error-pattern inspection) ---")
    for r in worst:
        print(f"PER={r['per']:.2f}  REF: {r['ref']}")
        print(f"         HYP: {r['hyp']}")
        print()