#!/usr/bin/env bash
set -euo pipefail

N="${1:-50}"
SEED="${2:-6493}"
OUTPUT_DIR="${3:-data/processed}"

python infer_exp/prepare_samples.py --n "$N" --seed "$SEED" --output_dir "$OUTPUT_DIR"
