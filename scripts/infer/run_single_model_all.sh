#!/usr/bin/env bash
set -euo pipefail

if [ "${1:-}" = "" ] || [ "${2:-}" = "" ]; then
  echo "Usage: bash scripts/infer/run_single_model_all.sh <CONFIG_YAML> <MODEL_ID> [MAX_SAMPLES] [ONLY_DATASETS] [ONLY_METHODS]"
  echo "Example: bash scripts/infer/run_single_model_all.sh configs/yaml/base.yaml Qwen/Qwen2.5-Math-1.5B-Instruct 30"
  exit 1
fi

CONFIG_PATH="$1"
MODEL_ID="$2"
MAX_SAMPLES="${3:-}"
ONLY_DATASETS="${4:-}"
ONLY_METHODS="${5:-}"

CMD=(python infer_exp/run_single_model_all.py --config "$CONFIG_PATH" --model_id "$MODEL_ID")

if [ "$MAX_SAMPLES" != "" ]; then
  CMD+=(--max_samples "$MAX_SAMPLES")
fi

if [ "$ONLY_DATASETS" != "" ]; then
  CMD+=(--only_datasets "$ONLY_DATASETS")
fi

if [ "$ONLY_METHODS" != "" ]; then
  CMD+=(--only_methods "$ONLY_METHODS")
fi

"${CMD[@]}"
