"""
Configuration helpers for experiment pipeline.
"""

import copy
from pathlib import Path
from typing import Any
from typing import Dict

import yaml


def _deep_merge_dict(
    base: Dict[str, Any],
    override: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Deep merge two dictionaries.

    Args:
        base: Base dictionary.
        override: Override dictionary.
    """
    merged = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge_dict(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def load_yaml_config(config_path: str) -> Dict[str, Any]:
    """
    Load YAML config with optional recursive "extends".

    Args:
        config_path: Config file path.
    """
    path = Path(config_path).resolve()
    with path.open(mode = "r", encoding = "utf-8") as file:
        config = yaml.safe_load(file) or {}

    parent = config.pop("extends", None)
    if not parent:
        return config

    parent_path = (path.parent / parent).resolve()
    parent_cfg = load_yaml_config(config_path = str(parent_path))
    return _deep_merge_dict(parent_cfg, config)


def ensure_dir(path: str) -> None:
    """
    Ensure target directory exists.

    Args:
        path: Directory path.
    """
    Path(path).mkdir(parents = True, exist_ok = True)
