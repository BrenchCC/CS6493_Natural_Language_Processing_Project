"""
Run all dataset batches for one specified model in a single command.
"""

import os
import sys
import copy
import argparse
import logging
from typing import Any
from typing import Dict
from typing import List

# Add project root to Python path
sys.path.append(os.getcwd())

from infer_exp.config_utils import load_yaml_config
from infer_exp.run_experiments import run_experiments


logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Args:
        None.
    """
    parser = argparse.ArgumentParser(
        description = "Run all dataset batches for one model."
    )
    parser.add_argument(
        "--config",
        type = str,
        required = True,
        help = "Path to base YAML config."
    )
    parser.add_argument(
        "--model_id",
        type = str,
        required = True,
        help = "Model id to run, e.g. Qwen/Qwen2.5-Math-1.5B-Instruct"
    )
    parser.add_argument(
        "--max_samples",
        type = int,
        default = None,
        help = "Optional override for max_samples on every dataset."
    )
    parser.add_argument(
        "--only_datasets",
        type = str,
        default = "",
        help = "Optional comma-separated dataset names to run."
    )
    parser.add_argument(
        "--only_methods",
        type = str,
        default = "",
        help = "Optional comma-separated method names to run."
    )
    return parser.parse_args()


def _parse_csv_names(csv_text: str) -> List[str]:
    """
    Parse comma-separated name list.

    Args:
        csv_text: Comma-separated text.
    """
    if not csv_text.strip():
        return []
    return [item.strip() for item in csv_text.split(",") if item.strip()]


def _dataset_name(dataset_cfg: Dict[str, Any]) -> str:
    """
    Get dataset name from dataset config.

    Args:
        dataset_cfg: Dataset config dictionary.
    """
    return str(dataset_cfg.get("name", ""))


def _method_name(method_entry: Any) -> str:
    """
    Get method name from method config entry.

    Args:
        method_entry: Method config entry (str or dict).
    """
    if isinstance(method_entry, str):
        return method_entry
    if isinstance(method_entry, dict):
        return str(method_entry.get("name", ""))
    return ""


def _filter_datasets(
    datasets: List[Dict[str, Any]],
    keep_names: List[str]
) -> List[Dict[str, Any]]:
    """
    Filter dataset configs by names.

    Args:
        datasets: Dataset config list.
        keep_names: Names to keep.
    """
    if not keep_names:
        return datasets
    keep_set = set(keep_names)
    return [item for item in datasets if _dataset_name(item) in keep_set]


def _filter_methods(
    methods: List[Any],
    keep_names: List[str]
) -> List[Any]:
    """
    Filter method config entries by names.

    Args:
        methods: Method config entry list.
        keep_names: Names to keep.
    """
    if not keep_names:
        return methods
    keep_set = set(keep_names)
    return [item for item in methods if _method_name(item) in keep_set]


def build_single_model_config(args: argparse.Namespace) -> Dict[str, Any]:
    """
    Build runtime config for one model execution.

    Args:
        args: Parsed command-line arguments.
    """
    base_cfg = load_yaml_config(args.config)
    cfg = copy.deepcopy(base_cfg)

    cfg["models"] = [{"id": args.model_id}]

    dataset_names = _parse_csv_names(args.only_datasets)
    method_names = _parse_csv_names(args.only_methods)

    cfg["datasets"] = _filter_datasets(cfg.get("datasets", []), dataset_names)
    cfg["methods"] = _filter_methods(cfg.get("methods", []), method_names)

    if args.max_samples is not None:
        for dataset_cfg in cfg.get("datasets", []):
            dataset_cfg["max_samples"] = int(args.max_samples)

    if not cfg.get("datasets"):
        raise ValueError("No datasets selected. Check --only_datasets.")
    if not cfg.get("methods"):
        raise ValueError("No methods selected. Check --only_methods.")

    return cfg


def main() -> None:
    """
    Run CLI entrypoint.

    Args:
        None.
    """
    args = parse_args()
    runtime_cfg = build_single_model_config(args)

    logger.info("Single-model run started.")
    logger.info("Model: %s", args.model_id)
    logger.info(
        "Datasets: %s",
        ", ".join([_dataset_name(item) for item in runtime_cfg.get("datasets", [])])
    )
    logger.info(
        "Methods: %s",
        ", ".join([_method_name(item) for item in runtime_cfg.get("methods", [])])
    )

    run_experiments(runtime_cfg)


if __name__ == "__main__":
    logging.basicConfig(
        level = logging.INFO,
        format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers = [logging.StreamHandler()]
    )
    main()
