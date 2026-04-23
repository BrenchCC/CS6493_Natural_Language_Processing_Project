"""Run the configured experiment matrix across models and methods."""

from __future__ import annotations

import argparse

from infer_exp.config_utils import load_experiment_config
from infer_exp.config_utils import parse_csv_filter
from infer_exp.run_single_model_all import run_one_model_one_method_all_datasets
from prompts import get_available_methods


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description = "Run the full experiment matrix.")
    parser.add_argument("--config", required = True, help = "Path to YAML config.")
    parser.add_argument("--models", default = "", help = "Comma-separated models override.")
    parser.add_argument("--methods", default = "", help = "Comma-separated methods override.")
    parser.add_argument("--datasets", default = "", help = "Comma-separated datasets override.")
    parser.add_argument("--max-samples", type = int, default = 0, help = "Optional max samples override.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_experiment_config(args.config)
    configured_models = list(config.get("models", {}).get("aliases", {}).keys())
    configured_methods = list(config.get("method_configs", {}).keys()) or get_available_methods()
    model_names = parse_csv_filter(args.models) or configured_models
    method_names = parse_csv_filter(args.methods) or configured_methods
    dataset_names = parse_csv_filter(args.datasets)
    max_samples = args.max_samples if args.max_samples > 0 else None

    for model_name in model_names:
        for method_name in method_names:
            run_one_model_one_method_all_datasets(
                config_path = args.config,
                model_name = model_name,
                method_name = method_name,
                max_samples = max_samples,
                dataset_filter = dataset_names,
            )


if __name__ == "__main__":
    main()
