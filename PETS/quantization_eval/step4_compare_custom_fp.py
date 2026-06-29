#!/usr/bin/env python3
"""Step 4 (custom): Compare baseline vs custom fixed-point quantized results."""
import json
import csv
import os

RESULTS_DIR = "./results"

with open(f'{RESULTS_DIR}/baseline_metrics.json') as f:
    baseline_metrics = json.load(f)
with open(f'{RESULTS_DIR}/custom_fp_metrics.json') as f:
    quantized_metrics = json.load(f)

with open(f'{RESULTS_DIR}/baseline_predictions.json') as f:
    baseline_preds = json.load(f)
with open(f'{RESULTS_DIR}/custom_fp_predictions.json') as f:
    quantized_preds = json.load(f)

assert len(baseline_preds) == len(quantized_preds), \
    f"Prediction count mismatch: {len(baseline_preds)} vs {len(quantized_preds)}"

agreement_count = 0
divergence_correct_to_wrong = 0
divergence_wrong_to_correct = 0
both_correct = 0
both_wrong = 0
both_wrong_same_pred = 0

for b, q in zip(baseline_preds, quantized_preds):
    assert b['text_idx'] == q['text_idx'], "Sample mismatch"
    assert b['position'] == q['position'], "Position mismatch"
    assert b['true_token_id'] == q['true_token_id'], "True token mismatch"

    b_correct = (b['top1_pred'] == b['true_token_id'])
    q_correct = (q['top1_pred'] == q['true_token_id'])
    same_pred = (b['top1_pred'] == q['top1_pred'])

    if same_pred:
        agreement_count += 1

    if b_correct and q_correct:
        both_correct += 1
    elif b_correct and not q_correct:
        divergence_correct_to_wrong += 1
    elif not b_correct and q_correct:
        divergence_wrong_to_correct += 1
    else:
        both_wrong += 1
        if same_pred:
            both_wrong_same_pred += 1

total = len(baseline_preds)
prediction_agreement = agreement_count / total * 100

print("=" * 70)
print("Custom Fixed-Point Quantization Impact Analysis")
print("=" * 70)
print(f"\nQuantization method: {quantized_metrics['quantization_method']}")
print(f"\nTotal masked tokens evaluated: {total}")
print(f"\nMetric            | Baseline (fp32) | Custom FP        | Change")
print(f"------------------|-----------------|------------------|--------")
print(f"Top-1 accuracy    | {baseline_metrics['metrics']['top1_accuracy_percent']:>13.2f}% | "
      f"{quantized_metrics['metrics']['top1_accuracy_percent']:>14.2f}% | "
      f"{quantized_metrics['metrics']['top1_accuracy_percent'] - baseline_metrics['metrics']['top1_accuracy_percent']:+.2f}pp")
print(f"Top-5 accuracy    | {baseline_metrics['metrics']['top5_accuracy_percent']:>13.2f}% | "
      f"{quantized_metrics['metrics']['top5_accuracy_percent']:>14.2f}% | "
      f"{quantized_metrics['metrics']['top5_accuracy_percent'] - baseline_metrics['metrics']['top5_accuracy_percent']:+.2f}pp")
print(f"Perplexity        | {baseline_metrics['metrics']['perplexity']:>14.4f} | "
      f"{quantized_metrics['metrics']['perplexity']:>15.4f} | "
      f"{quantized_metrics['metrics']['perplexity'] - baseline_metrics['metrics']['perplexity']:+.4f}")

print(f"\nPrediction Agreement Analysis:")
print(f"  Same top-1 prediction (agreement): {prediction_agreement:.2f}% ({agreement_count}/{total})")
print(f"  Both correct: {both_correct / total * 100:.2f}% ({both_correct}/{total})")
print(f"  Both wrong: {both_wrong / total * 100:.2f}% ({both_wrong}/{total})")
print(f"    - same wrong prediction: {both_wrong_same_pred / total * 100:.2f}% ({both_wrong_same_pred}/{total})")
print(f"  Baseline correct -> Quantized wrong: {divergence_correct_to_wrong / total * 100:.2f}% ({divergence_correct_to_wrong}/{total})")
print(f"  Baseline wrong -> Quantized correct: {divergence_wrong_to_correct / total * 100:.2f}% ({divergence_wrong_to_correct}/{total})")

# 이전 PyTorch int8 결과와도 비교
pytorch_int8_path = f'{RESULTS_DIR}/quantized_metrics.json'
if os.path.exists(pytorch_int8_path):
    with open(pytorch_int8_path) as f:
        pytorch_int8 = json.load(f)

    print(f"\n{'='*70}")
    print("Comparison with PyTorch int8 (previous measurement)")
    print(f"{'='*70}")
    print(f"\nMetric          | PyTorch int8     | Custom FP        | Difference")
    print(f"----------------|------------------|------------------|------------------")
    print(f"Top-1 accuracy  | {pytorch_int8['metrics']['top1_accuracy_percent']:>14.2f}% | "
          f"{quantized_metrics['metrics']['top1_accuracy_percent']:>14.2f}% | "
          f"{quantized_metrics['metrics']['top1_accuracy_percent'] - pytorch_int8['metrics']['top1_accuracy_percent']:+.2f}pp")
    print(f"Top-5 accuracy  | {pytorch_int8['metrics']['top5_accuracy_percent']:>14.2f}% | "
          f"{quantized_metrics['metrics']['top5_accuracy_percent']:>14.2f}% | "
          f"{quantized_metrics['metrics']['top5_accuracy_percent'] - pytorch_int8['metrics']['top5_accuracy_percent']:+.2f}pp")
    print(f"Perplexity      | {pytorch_int8['metrics']['perplexity']:>15.4f} | "
          f"{quantized_metrics['metrics']['perplexity']:>15.4f} | "
          f"{quantized_metrics['metrics']['perplexity'] - pytorch_int8['metrics']['perplexity']:+.4f}")

comparison = {
    'evaluation_setup': {
        'model': 'uw-madison/nystromformer-512',
        'dataset': 'WikiText-103 validation',
        'num_eval_texts': baseline_metrics['num_eval_texts'],
        'total_masked_tokens': total,
        'mask_probability': baseline_metrics['mask_probability'],
        'seed': baseline_metrics['seed'],
    },
    'baseline': baseline_metrics['metrics'],
    'custom_fp_quantized': quantized_metrics['metrics'],
    'quantization_method': quantized_metrics['quantization_method'],
    'quantization_params': quantized_metrics['quantization_params'],
    'differences': {
        'top1_accuracy_change_pp': quantized_metrics['metrics']['top1_accuracy_percent'] - baseline_metrics['metrics']['top1_accuracy_percent'],
        'top5_accuracy_change_pp': quantized_metrics['metrics']['top5_accuracy_percent'] - baseline_metrics['metrics']['top5_accuracy_percent'],
        'perplexity_change': quantized_metrics['metrics']['perplexity'] - baseline_metrics['metrics']['perplexity'],
        'perplexity_relative_change_percent': (quantized_metrics['metrics']['perplexity'] - baseline_metrics['metrics']['perplexity']) / baseline_metrics['metrics']['perplexity'] * 100,
    },
    'prediction_agreement': {
        'same_top1_prediction_percent': prediction_agreement,
        'both_correct_percent': both_correct / total * 100,
        'both_wrong_percent': both_wrong / total * 100,
        'both_wrong_same_pred_percent': both_wrong_same_pred / total * 100,
        'baseline_correct_quantized_wrong_percent': divergence_correct_to_wrong / total * 100,
        'baseline_wrong_quantized_correct_percent': divergence_wrong_to_correct / total * 100,
    },
}

with open(f'{RESULTS_DIR}/custom_fp_comparison.json', 'w') as f:
    json.dump(comparison, f, indent=2)

with open(f'{RESULTS_DIR}/custom_fp_comparison.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Metric', 'Baseline (float32)', quantized_metrics['quantization_method'], 'Change'])
    writer.writerow([
        'Top-1 MLM accuracy (%)',
        f"{baseline_metrics['metrics']['top1_accuracy_percent']:.2f}",
        f"{quantized_metrics['metrics']['top1_accuracy_percent']:.2f}",
        f"{quantized_metrics['metrics']['top1_accuracy_percent'] - baseline_metrics['metrics']['top1_accuracy_percent']:+.2f}pp"
    ])
    writer.writerow([
        'Top-5 MLM accuracy (%)',
        f"{baseline_metrics['metrics']['top5_accuracy_percent']:.2f}",
        f"{quantized_metrics['metrics']['top5_accuracy_percent']:.2f}",
        f"{quantized_metrics['metrics']['top5_accuracy_percent'] - baseline_metrics['metrics']['top5_accuracy_percent']:+.2f}pp"
    ])
    writer.writerow([
        'Perplexity',
        f"{baseline_metrics['metrics']['perplexity']:.4f}",
        f"{quantized_metrics['metrics']['perplexity']:.4f}",
        f"{quantized_metrics['metrics']['perplexity'] - baseline_metrics['metrics']['perplexity']:+.4f}"
    ])
    writer.writerow([
        'Prediction agreement (%)',
        '-',
        '-',
        f"{prediction_agreement:.2f}"
    ])

print(f"\n{'='*70}")
print(f"Results saved to:")
print(f"  {RESULTS_DIR}/custom_fp_comparison.json")
print(f"  {RESULTS_DIR}/custom_fp_comparison.csv")
print(f"{'='*70}")
