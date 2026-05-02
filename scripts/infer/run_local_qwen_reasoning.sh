#!/usr/bin/env bash
set -euo pipefail

CONFIG_PATH="${1:-configs/yaml/qwen_math.yaml}"
MODEL_NAME="${2:-Qwen/Qwen2.5-Math-1.5B-Instruct}"
MAX_SAMPLES="${3:-50}"
DATASETS="${4:-}"
METHODS="${5:-tir,plan_solve,self_ask}"

CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0,1}" \
python -m infer_exp.run_single_model_all \
  --config "$CONFIG_PATH" \
  --model "$MODEL_NAME" \
  --max-samples "$MAX_SAMPLES" \
  --datasets "$DATASETS" \
  --methods "$METHODS" \
  --backend vllm

