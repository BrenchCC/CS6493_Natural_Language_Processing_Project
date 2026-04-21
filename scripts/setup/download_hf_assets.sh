#!/usr/bin/env bash
set -euo pipefail

CACHE_DIR="${1:-models/hf_cache}"
mkdir -p "$CACHE_DIR"

if ! command -v huggingface-cli >/dev/null 2>&1; then
  echo "huggingface-cli not found. Install first: pip install -U huggingface_hub"
  exit 1
fi

echo "Downloading models to: $CACHE_DIR"
huggingface-cli download Qwen/Qwen2.5-Math-1.5B-Instruct --local-dir "$CACHE_DIR/Qwen2.5-Math-1.5B-Instruct"
huggingface-cli download deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B --local-dir "$CACHE_DIR/DeepSeek-R1-Distill-Qwen-1.5B"
echo "Download finished."
