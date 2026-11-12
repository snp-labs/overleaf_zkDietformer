# zkDietFormer

Zero-knowledge verification framework for low-rank self-attention in Transformers.

## Directory Structure

| Folder | Target | Scope | Note |
|--------|--------|-------|------|
| **ASIACCS** | ASIACCS 2027 | Nystromformer, Linformer, SOFT | Generalized to multiple low-rank attention mechanisms |
| **ICISC** | ICISC | Nystromformer only | Most clearly written among the single-model versions |
| **PETS** | PETS | Nystromformer only | |
| **FC** | FC | Nystromformer only | |
| **USENIX** | USENIX Security | Nystromformer only | Early draft |
| **results** | - | - | Shared experiment logs (`.time`, `.json`) |
| **images** | - | - | Shared figures |

## Experiment Data Mapping

All papers hardcode experiment values into `.tex` tables. The raw data lives under `results/`.

| Results Folder | Contents | Used By |
|----------------|----------|---------|
| `results_nystrom/tiny_circuit/` | Nystromformer & BERT full-pipeline benchmarks (2026-09-17) | ASIACCS |
| `tiny_results_with_global_qkvyz_midtemp/` | Nystromformer & BERT full-pipeline benchmarks (2026-08-14~15) | ICISC, FC, PETS |
| `results_onlyeq/` | Attention-only benchmarks for multi-spec scaling figures (2026-08-18~20) | ASIACCS, ICISC, FC, PETS |
| `results_softlinformer/` | Linformer & SOFT benchmarks (2026-09-14) | ASIACCS |
| `quantization_results/` | Quantization fidelity evaluation (`.json`) | ASIACCS, ICISC, FC, PETS |

USENIX is an early draft with no experiment tables; it does not reference any results data.
