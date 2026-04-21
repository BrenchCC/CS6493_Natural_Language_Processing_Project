#!/usr/bin/env bash
set -euo pipefail

if [ "${1:-}" = "" ]; then
  echo "Usage: bash scripts/eval/summarize_scores.sh <CONFIG_YAML>"
  exit 1
fi

CONFIG_PATH="$1"
python evaluation/summarize_scores.py --config "$CONFIG_PATH"
