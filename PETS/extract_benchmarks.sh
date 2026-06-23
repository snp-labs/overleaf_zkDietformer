#!/usr/bin/env python3
"""Extract and aggregate benchmark data from PETS result directories.
Sums across all layers for total model cost."""

import os
import json
import glob
import re

RESULTS_DIR = "/Users/minhae/Projects/overleaf/zkDietformer/PETS/results"

# Directory configs: (dir_name, L, d, label)
DIRS = [
    ("tiny_results",   2,  128, "L=2, d=128"),
    ("mini_results",   4,  256, "L=4, d=256"),
    ("small_results",  4,  512, "L=4, d=512"),
    ("medium_results", 8,  512, "L=8, d=512"),
    ("base_results",  12,  768, "L=12, d=768"),
]

CIRCUIT_TYPES = [
    "nystrom_attn_freivalds",
    "nystrom_attn_naive",
    "bert_attn_freivalds",
    "bert_attn_naive",
    "nystrom_mlp",
    "bert_mlp",
]

SEQ_LENS = [128, 256, 512, 1024, 2048, 4096]


def find_best_log(dir_path, pattern, expected_layers):
    """Find the best log file: prefer latest with complete results, then latest with any results."""
    files = sorted(glob.glob(os.path.join(dir_path, pattern)), reverse=True)
    if not files:
        return None

    # First pass: find latest with expected number of BENCHMARK_RESULT lines
    for f in files:
        count = count_benchmarks(f)
        if count == expected_layers:
            return f

    # Second pass: find latest with ANY BENCHMARK_RESULT lines
    for f in files:
        count = count_benchmarks(f)
        if count > 0:
            return f

    # No file with results - return latest (will be marked OOM)
    return files[0]


def count_benchmarks(logfile):
    """Count BENCHMARK_RESULT lines in a log file."""
    count = 0
    try:
        with open(logfile, 'r') as f:
            for line in f:
                if 'BENCHMARK_RESULT' in line:
                    count += 1
    except:
        pass
    return count


def extract_memory_gb(timefile):
    """Extract memory from .time file. macOS reports bytes."""
    if not os.path.exists(timefile):
        return None
    try:
        with open(timefile, 'r') as f:
            for line in f:
                if 'maximum resident set size' in line:
                    val = int(line.strip().split()[0])
                    return val / 1e9
    except:
        pass
    return None


def parse_benchmarks(logfile):
    """Parse BENCHMARK_RESULT lines and aggregate across all layers."""
    total_setup_ms = 0
    total_prove_ms = 0
    total_verify_ms = 0
    constraints = 0
    layer_count = 0

    with open(logfile, 'r') as f:
        for line in f:
            if 'BENCHMARK_RESULT' not in line:
                continue
            json_str = line.strip()[len('BENCHMARK_RESULT '):]
            try:
                data = json.loads(json_str)
            except json.JSONDecodeError:
                continue

            layer_count += 1
            constraints = data.get('constraints', 0)
            setup_ms = data.get('setup_ms', 0)
            cp_link = data.get('cp_link', {})
            groth16 = data.get('groth16', {})
            lasso = data.get('lasso', {})

            total_setup_ms += setup_ms + cp_link.get('setup_ms', 0)
            total_prove_ms += groth16.get('prove_ms', 0) + lasso.get('total_ms', 0) + cp_link.get('prove_ms', 0)
            total_verify_ms += groth16.get('verify_ms', 0) + cp_link.get('verify_ms', 0)

    return {
        'constraints': constraints,
        'setup_s': total_setup_ms / 1000.0,
        'prove_s': total_prove_ms / 1000.0,
        'verify_ms': total_verify_ms,
        'layer_count': layer_count,
    }


def check_oom(logfile):
    """Check if log file indicates OOM."""
    try:
        with open(logfile, 'r') as f:
            content = f.read()
            if 'OOM' in content or 'out of memory' in content.lower() or 'Cannot allocate memory' in content:
                return True
    except:
        pass
    return False


def main():
    for dir_name, expected_L, d, label in DIRS:
        dir_path = os.path.join(RESULTS_DIR, dir_name)
        if not os.path.isdir(dir_path):
            print(f"Directory not found: {dir_path}")
            continue

        print()
        print(f"=== {dir_name} ({label}) ===")
        print()

        for circuit in CIRCUIT_TYPES:
            has_any = False
            results = []

            for n in SEQ_LENS:
                # Build file pattern
                if circuit.startswith("nystrom_"):
                    pattern = f"prove_{circuit}_n{n}_m32_*.log"
                else:
                    pattern = f"prove_{circuit}_n{n}_L*.log"

                logfile = find_best_log(dir_path, pattern, expected_L)
                if logfile is None:
                    continue

                has_any = True
                timefile = logfile.replace('.log', '.time')

                # Check for OOM / missing benchmarks
                bench_count = count_benchmarks(logfile)
                if bench_count == 0:
                    results.append(f"  n={n}: OOM (no results)")
                    continue

                # Parse benchmarks
                data = parse_benchmarks(logfile)
                mem = extract_memory_gb(timefile)

                # Format memory
                mem_str = f"{mem:.1f}" if mem is not None else "N/A"

                # Check completeness
                incomplete = ""
                if data['layer_count'] < expected_L:
                    incomplete = f" [INCOMPLETE: {data['layer_count']}/{expected_L} layers]"

                results.append(
                    f"  n={n}: constraints={data['constraints']}, "
                    f"setup={data['setup_s']:.1f}s, "
                    f"prove={data['prove_s']:.1f}s, "
                    f"verify={data['verify_ms']:.0f}ms, "
                    f"mem={mem_str}GB{incomplete}"
                )

            if has_any:
                print(f"{circuit}:")
                for r in results:
                    print(r)
                print()


if __name__ == '__main__':
    main()
