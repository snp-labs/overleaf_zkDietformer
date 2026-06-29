#!/usr/bin/env python3
"""Step 2: Evaluate baseline (float32) Nystromformer on MLM task."""
import torch
import torch.nn.functional as F
import numpy as np
import json
import random
import os
from transformers import AutoTokenizer, NystromformerForMaskedLM
from datasets import load_dataset
from tqdm import tqdm

MODEL_NAME = "uw-madison/nystromformer-512"
OUTPUT_DIR = "./results"
SEED = 42
NUM_SAMPLES = 1000
MASK_PROBABILITY = 0.15
MIN_TOKENS = 20
MAX_LENGTH = 128

os.makedirs(OUTPUT_DIR, exist_ok=True)

random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = NystromformerForMaskedLM.from_pretrained(MODEL_NAME)
model.eval()

device = torch.device('cpu')
model = model.to(device)

print("Loading WikiText-103 validation set...")
dataset = load_dataset('wikitext', 'wikitext-103-v1', split='validation')

valid_texts = [
    t for t in dataset['text']
    if t.strip() and len(t.strip().split()) >= MIN_TOKENS
]
random.shuffle(valid_texts)
eval_texts = valid_texts[:NUM_SAMPLES]
print(f"Using {len(eval_texts)} texts for evaluation")

mask_token_id = tokenizer.mask_token_id

total_masked = 0
correct_top1 = 0
correct_top5 = 0
log_prob_sum = 0.0

all_predictions = []

for text_idx, text in enumerate(tqdm(eval_texts, desc="Baseline eval")):
    encoded = tokenizer(
        text,
        return_tensors='pt',
        max_length=MAX_LENGTH,
        truncation=True,
        padding=False,
    )
    input_ids = encoded['input_ids'][0]

    if len(input_ids) < 5:
        continue

    special_token_ids = {
        tokenizer.cls_token_id,
        tokenizer.sep_token_id,
        tokenizer.pad_token_id,
    }

    maskable_positions = [
        i for i, tok_id in enumerate(input_ids.tolist())
        if tok_id not in special_token_ids
    ]

    if len(maskable_positions) == 0:
        continue

    num_to_mask = max(1, int(len(maskable_positions) * MASK_PROBABILITY))
    masked_positions = random.sample(maskable_positions, num_to_mask)

    true_token_ids = [input_ids[pos].item() for pos in masked_positions]

    masked_input_ids = input_ids.clone()
    for pos in masked_positions:
        masked_input_ids[pos] = mask_token_id

    masked_input_ids = masked_input_ids.unsqueeze(0).to(device)

    with torch.no_grad():
        outputs = model(input_ids=masked_input_ids)
        logits = outputs.logits[0]

    for pos, true_id in zip(masked_positions, true_token_ids):
        pred_logits = logits[pos]

        top1_id = pred_logits.argmax().item()
        if top1_id == true_id:
            correct_top1 += 1

        top5_ids = pred_logits.topk(5).indices.tolist()
        if true_id in top5_ids:
            correct_top5 += 1

        log_probs = F.log_softmax(pred_logits, dim=-1)
        log_prob_sum += log_probs[true_id].item()

        all_predictions.append({
            'text_idx': text_idx,
            'position': pos,
            'true_token_id': true_id,
            'top1_pred': top1_id,
        })

        total_masked += 1

top1_accuracy = correct_top1 / total_masked * 100
top5_accuracy = correct_top5 / total_masked * 100
average_log_prob = log_prob_sum / total_masked
perplexity = np.exp(-average_log_prob)

print(f"\n{'='*60}")
print(f"Baseline (float32) results:")
print(f"{'='*60}")
print(f"Total masked tokens evaluated: {total_masked}")
print(f"Top-1 accuracy: {top1_accuracy:.2f}%")
print(f"Top-5 accuracy: {top5_accuracy:.2f}%")
print(f"Perplexity: {perplexity:.4f}")

results = {
    'configuration': 'uw-madison/nystromformer-512 (float32 baseline)',
    'dataset': 'WikiText-103 validation',
    'num_eval_texts': len(eval_texts),
    'mask_probability': MASK_PROBABILITY,
    'total_masked_tokens': total_masked,
    'metrics': {
        'top1_accuracy_percent': top1_accuracy,
        'top5_accuracy_percent': top5_accuracy,
        'perplexity': float(perplexity),
        'average_log_prob': float(average_log_prob),
    },
    'seed': SEED,
    'max_length': MAX_LENGTH,
    'min_tokens': MIN_TOKENS,
}

with open(f'{OUTPUT_DIR}/baseline_metrics.json', 'w') as f:
    json.dump(results, f, indent=2)

with open(f'{OUTPUT_DIR}/baseline_predictions.json', 'w') as f:
    json.dump(all_predictions, f)

print(f"\nResults saved to {OUTPUT_DIR}/")
