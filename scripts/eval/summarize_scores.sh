#!/usr/bin/env bash
set -euo pipefail

CONFIG_PATH="${1:-configs/yaml/base.yaml}"

python -m evaluation.summarize_scores --config "$CONFIG_PATH"
