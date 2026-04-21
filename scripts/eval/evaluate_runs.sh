#!/usr/bin/env bash
set -euo pipefail

if [ "${1:-}" = "" ]; then
  echo "Usage: bash scripts/eval/evaluate_runs.sh <CONFIG_YAML>"
  exit 1
fi

CONFIG_PATH="$1"
python evaluation/evaluate_runs.py --config "$CONFIG_PATH"
