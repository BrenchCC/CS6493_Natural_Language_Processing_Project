"""Configuration helpers for experiment orchestration."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from typing import Dict
from typing import Iterable
from typing import List

import yaml


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _resolve_path(path_like: str) -> str:
    path = Path(path_like)
    if path.is_absolute():
        return str(path)
    return str((PROJECT_ROOT / path).resolve())


def load_experiment_config(config_path: str) -> Dict[str, Any]:
    """Load and normalize YAML config."""
    resolved_config_path = _resolve_path(config_path)
    with open(resolved_config_path, "r", encoding = "utf-8") as file:
        config = yaml.safe_load(file) or {}

    run_config = config.setdefault("run", {})
    run_config.setdefault("output_dir", "results/raw")
    run_config.setdefault("evaluated_dir", "results/evaluated")
    run_config.setdefault("summary_dir", "results/summaries")
    run_config.setdefault("log_dir", "results/logs")
    run_config["output_dir"] = _resolve_path(run_config["output_dir"])
    run_config["evaluated_dir"] = _resolve_path(run_config["evaluated_dir"])
    run_config["summary_dir"] = _resolve_path(run_config["summary_dir"])
    run_config["log_dir"] = _resolve_path(run_config["log_dir"])

    datasets = config.setdefault("datasets", [])
    for dataset in datasets:
        dataset["sample_path"] = _resolve_path(dataset["sample_path"])

    return config


def parse_csv_filter(raw_value: str | None) -> List[str]:
    """Split a comma-separated CLI filter into a clean list."""
    if not raw_value:
        return []
    return [item.strip() for item in raw_value.split(",") if item.strip()]


def filter_named_items(items: Iterable[Dict[str, Any]], names: List[str], key: str = "name") -> List[Dict[str, Any]]:
    """Filter config dictionaries by a list of names."""
    if not names:
        return list(items)
    name_set = set(names)
    return [item for item in items if item.get(key) in name_set]


def resolve_model_path(config: Dict[str, Any], model_name: str) -> str:
    """Resolve a model alias to an existing local path when possible."""
    models_config = config.get("models", {})
    aliases = models_config.get("aliases", {})
    if model_name in aliases:
        return _resolve_path(aliases[model_name])

    candidate_paths = [
        Path(model_name),
        PROJECT_ROOT / model_name,
        PROJECT_ROOT / "models" / Path(model_name).name,
    ]
    for candidate in candidate_paths:
        if candidate.exists():
            return str(candidate.resolve())
    return model_name


def model_alias(model_name: str) -> str:
    """Convert a model name into a filesystem-friendly alias."""
    alias = Path(model_name).name or model_name
    return alias.replace("/", "-")


def get_model_settings(config: Dict[str, Any], model_name: str) -> Dict[str, Any]:
    """Return normalized runtime settings for a model."""
    settings = config.get("models", {}).get("settings", {}).get(model_name, {})
    normalized = dict(settings)
    normalized.setdefault("reasoning_mode", "prompt_cot")
    normalized.setdefault("enable_thinking", None)
    normalized.setdefault("cannot_disable_thinking", False)
    return normalized
