#!/usr/bin/env bash
set -euo pipefail

CONFIG_PATH="${1:-configs/yaml/api_deepseek_r1_math.yaml}"
MAX_SAMPLES="${2:-50}"
DATASETS="${3:-}"
METHODS="${4:-tir,plan_solve,self_ask}"

if [[ ! -f ".env" ]]; then
  echo "Missing .env. Please run this script from the project root." >&2
  exit 1
fi

python -m infer_exp.run_single_model_all \
  --config "$CONFIG_PATH" \
  --model "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B" \
  --backend api \
  --max-samples "$MAX_SAMPLES" \
  --datasets "$DATASETS" \
  --methods "$METHODS"
