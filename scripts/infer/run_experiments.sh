#!/usr/bin/env bash
set -euo pipefail

CONFIG_PATH="${1:-configs/yaml/base.yaml}"
MODELS="${2:-}"
METHODS="${3:-}"
DATASETS="${4:-}"
MAX_SAMPLES="${5:-0}"

python -m infer_exp.run_experiments \
  --config "$CONFIG_PATH" \
  --models "$MODELS" \
  --methods "$METHODS" \
  --datasets "$DATASETS" \
  --max-samples "$MAX_SAMPLES"
