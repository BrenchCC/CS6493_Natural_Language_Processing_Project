#!/usr/bin/env bash
set -euo pipefail

CONFIG_PATH="${1:-configs/yaml/deepseek_r1_math.yaml}"
MODEL_NAME="${2:-deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B}"
MAX_SAMPLES="${3:-50}"
DATASETS="${4:-}"
METHODS="${5:-tir,plan_solve,self_ask}"

CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-2,3}" \
python -m infer_exp.run_single_model_all \
  --config "$CONFIG_PATH" \
  --model "$MODEL_NAME" \
  --max-samples "$MAX_SAMPLES" \
  --datasets "$DATASETS" \
  --methods "$METHODS" \
  --backend vllm

