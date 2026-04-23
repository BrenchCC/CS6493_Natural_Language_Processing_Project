"""Prompt method registry."""

from typing import Any
from typing import Dict

from .cot_zero import CoTZero
from .cot_few_shot import CoTFewShot
from .self_refine import SelfRefine
from .self_consistent import SelfConsistency
from .tir import ToolIntegratedReasoning


METHOD_REGISTRY = {
    "cot_zero": CoTZero,
    "cot_few_shot": CoTFewShot,
    "self_refine": SelfRefine,
    "self_consistency": SelfConsistency,
    "tir": ToolIntegratedReasoning,
}


def get_prompt_method(method_name: str, method_config: Dict[str, Any] = None):
    """Build prompt method by method name."""
    if method_name not in METHOD_REGISTRY:
        raise ValueError(f"Unsupported prompt method: {method_name}")
    return METHOD_REGISTRY[method_name](config = method_config or {})


def get_available_methods() -> list[str]:
    """Return all registered prompt methods."""
    return list(METHOD_REGISTRY.keys())
