#!/usr/bin/env bash
set -euo pipefail

if [ "${1:-}" = "" ]; then
  echo "Usage: bash scripts/vllm/run_local_infer.sh <CONFIG_YAML>"
  exit 1
fi

CONFIG_PATH="$1"
bash scripts/infer/run_experiments.sh "$CONFIG_PATH"
