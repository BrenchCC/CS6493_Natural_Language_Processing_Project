#!/usr/bin/env bash
set -euo pipefail

ENV_NAME="${1:-}"
REQ_FILE="${2:-requirements.topic1.txt}"

if [ ! -f "$REQ_FILE" ]; then
  echo "Requirements file not found: $REQ_FILE"
  exit 1
fi

if [ "$ENV_NAME" = "" ]; then
  echo "Installing with current python environment..."
  pip install -r "$REQ_FILE"
  exit 0
fi

if ! command -v conda >/dev/null 2>&1; then
  echo "Conda not found. Install Conda first or run without ENV_NAME."
  exit 1
fi

echo "Installing into conda environment: $ENV_NAME"
conda run -n "$ENV_NAME" pip install -r "$REQ_FILE"
