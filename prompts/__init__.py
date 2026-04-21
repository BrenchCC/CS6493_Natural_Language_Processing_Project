"""
Prompt method registry.
"""

from typing import Any
from typing import Dict

from .cot_zero import CoTZeroShot
from .cot_few_shot import CoTFewShot
from .self_refine import SelfRefine
from .self_consistency import SelfConsistency
from .tir import ToolIntegratedReasoning
from .sr_sd_tir import SkillRoutedSelfDiscoverTIR


METHOD_REGISTRY = {
    "cot_zero": CoTZeroShot,
    "cot_few_shot": CoTFewShot,
    "self_refine": SelfRefine,
    "self_consistency": SelfConsistency,
    "tir": ToolIntegratedReasoning,
    "sr_sd_tir": SkillRoutedSelfDiscoverTIR
}


def get_prompt_method(method_name: str, method_config: Dict[str, Any] = None):
    """
    Build prompt method by method name.

    Args:
        method_name: Registered prompt method key.
        method_config: Method-level configuration dictionary.
    """
    if method_name not in METHOD_REGISTRY:
        raise ValueError(f"Unsupported prompt method: {method_name}")
    return METHOD_REGISTRY[method_name](config = method_config or {})
