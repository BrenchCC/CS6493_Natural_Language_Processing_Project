#!/usr/bin/env bash
set -euo pipefail

if [ "${1:-}" = "" ]; then
  echo "Usage: bash scripts/infer/run_experiments.sh <CONFIG_YAML>"
  exit 1
fi

CONFIG_PATH="$1"
python infer_exp/run_experiments.py --config "$CONFIG_PATH"
