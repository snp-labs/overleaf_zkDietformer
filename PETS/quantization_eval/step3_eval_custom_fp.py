#!/usr/bin/env python3
"""
Step 3 (custom): Evaluate Nystromformer with zkDietFormer's custom fixed-point
quantization applied to all weights and activations.

Quantization scheme matches quantize.py exactly:
  - 8-bit unsigned affine per-tensor quantization
  - scale = (max(0, data_max) - min(0, data_min)) / 255
  - zero_point = round(-min / scale), clamped to [0, 255]
  - Q = floor(data / scale + zero_point), clipped to [0, 255]
  - Dequantize: data_approx = (Q - zero_point) * scale

This simulates the quantization error introduced by the ZK circuit.
"""
import torch
import torch.nn as nn
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
QUANT_BITS = 8  # matches quantize.py default

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Reproducibility (baseline과 동일 seed)
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)


# ============================================================
# quantize.py의 양자화 로직을 PyTorch native로 재현
# ============================================================
def quantize_dequantize_tensor(tensor, bits=QUANT_BITS):
    """
    quantize.py의 get_quantization_params + quantize_tensor을 정확히 재현한 뒤
    dequantize하여 float로 되돌림.

    이 round-trip이 ZK 서킷이 도입하는 양자화 오차를 시뮬레이션.
    """
    with torch.no_grad():
        # get_quantization_params 재현
        data_min = tensor.min().item()
        data_max = tensor.max().item()
        rmin = min(0.0, data_min)
        rmax = max(0.0, data_max)

        qmin = 0
        qmax = (1 << bits) - 1

        scale = (rmax - rmin) / (qmax - qmin)
        if scale == 0:
            scale = 1e-9

        initial_zp = qmin - rmin / scale
        zero_point = round(initial_zp)
        zero_point = max(qmin, min(qmax, zero_point))

        # quantize_tensor 재현
        q_data = torch.floor(tensor / scale + zero_point)
        q_data = torch.clamp(q_data, qmin, qmax)

        # dequantize
        return (q_data - zero_point) * scale


def apply_custom_fp_quantization(model, bits=QUANT_BITS):
    """
    모든 weights를 quantize-dequantize하고,
    모든 Linear/LayerNorm 출력에 activation quantize-dequantize hook 등록.
    """
    # 1. Weight quantization (정적)
    with torch.no_grad():
        for name, param in model.named_parameters():
            param.data = quantize_dequantize_tensor(param.data, bits)

    # 2. Activation quantization (forward hook)
    hooks = []

    def make_hook(module_name):
        def activation_quant_hook(module, input, output):
            if isinstance(output, torch.Tensor):
                return quantize_dequantize_tensor(output, bits)
            elif isinstance(output, tuple):
                return tuple(
                    quantize_dequantize_tensor(o, bits) if isinstance(o, torch.Tensor) else o
                    for o in output
                )
            return output
        return activation_quant_hook

    for name, module in model.named_modules():
        if isinstance(module, (nn.Linear, nn.LayerNorm)):
            h = module.register_forward_hook(make_hook(name))
            hooks.append(h)

    return model, hooks


# ============================================================
# Model and tokenizer
# ============================================================
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = NystromformerForMaskedLM.from_pretrained(MODEL_NAME)
model.eval()

# Custom fixed-point quantization 적용
print(f"Applying custom fixed-point quantization ({QUANT_BITS}-bit per-tensor affine)")
print(f"Quantization scheme matches quantize.py: get_quantization_params + quantize_tensor")
model_quantized, hooks = apply_custom_fp_quantization(model, bits=QUANT_BITS)

quantization_method = f'Custom fixed-point ({QUANT_BITS}-bit per-tensor affine, matching quantize.py)'

# Forward pass 검증
print("Verifying forward pass with quantized model...")
dummy_input = torch.randint(0, 1000, (1, 32))
with torch.no_grad():
    dummy_output = model_quantized(input_ids=dummy_input)
print(f"Forward pass OK. Output shape: {dummy_output.logits.shape}")

# Device (hooks 사용하므로 CPU에서 실행)
device = torch.device('cpu')
model_quantized = model_quantized.to(device)
print(f"Using device: {device}")

# Dataset (baseline과 동일)
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

for text_idx, text in enumerate(tqdm(eval_texts, desc="Custom FP eval")):
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
        outputs = model_quantized(input_ids=masked_input_ids)
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

# Hook 제거
for h in hooks:
    h.remove()

top1_accuracy = correct_top1 / total_masked * 100
top5_accuracy = correct_top5 / total_masked * 100
average_log_prob = log_prob_sum / total_masked
perplexity = np.exp(-average_log_prob)

print(f"\n{'='*60}")
print(f"Custom fixed-point quantized results:")
print(f"{'='*60}")
print(f"Quantization: {quantization_method}")
print(f"Total masked tokens evaluated: {total_masked}")
print(f"Top-1 accuracy: {top1_accuracy:.2f}%")
print(f"Top-5 accuracy: {top5_accuracy:.2f}%")
print(f"Perplexity: {perplexity:.4f}")

results = {
    'configuration': f'uw-madison/nystromformer-512 ({quantization_method})',
    'quantization_method': quantization_method,
    'quantization_params': {
        'bits': QUANT_BITS,
        'type': 'per-tensor affine unsigned',
        'range': f'[0, {(1 << QUANT_BITS) - 1}]',
        'source': 'quantize.py from zkDietFormer project',
        'weight_quantization': True,
        'activation_quantization': True,
        'target_layers': 'nn.Linear, nn.LayerNorm',
    },
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

with open(f'{OUTPUT_DIR}/custom_fp_metrics.json', 'w') as f:
    json.dump(results, f, indent=2)

with open(f'{OUTPUT_DIR}/custom_fp_predictions.json', 'w') as f:
    json.dump(all_predictions, f)

print(f"\nResults saved to {OUTPUT_DIR}/")
