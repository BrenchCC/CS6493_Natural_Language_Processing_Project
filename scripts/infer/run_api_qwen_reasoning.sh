#!/usr/bin/env bash
set -euo pipefail

CONFIG_PATH="${1:-configs/yaml/api_qwen_math_reasoning_usage.yaml}"
MAX_SAMPLES="${2:-50}"
DATASETS="${3:-}"
METHODS="${4:-plan_solve,tir}"

if [[ ! -f ".env" ]]; then
  echo "Missing .env. Please run this script from the project root." >&2
  exit 1
fi

python -m infer_exp.run_single_model_all \
  --config "$CONFIG_PATH" \
  --model "Qwen/Qwen2.5-Math-1.5B-Instruct" \
  --backend api \
  --max-samples "$MAX_SAMPLES" \
  --datasets "$DATASETS" \
  --methods "$METHODS"
