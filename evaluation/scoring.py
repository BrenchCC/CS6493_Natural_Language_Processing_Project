"""
Score calculation utilities with range constraint [0, 1].
"""

import math
from typing import Any
from typing import Dict


DEFAULT_SCORING_CONFIG = {
    "weights": {
        "answer": 0.3,
        "length": 0.4,
        "reflection": 0.3
    },
    "params": {
        "a_star": 2.0,
        "tau_a": 2.0,
        "r_star": 2.0,
        "tau_r": 2.0,
        "rho_star": 0.25,
        "tau_tail": 0.20,
        "L_ref": 256.0,
        "tau_d": 256.0
    }
}


def _safe_positive(value: Any, fallback: float) -> float:
    """
    Return positive float value with fallback.

    Args:
        value: Candidate numeric value.
        fallback: Fallback value if invalid.
    """
    try:
        parsed = float(value)
    except Exception:
        return fallback
    if parsed <= 0:
        return fallback
    return parsed


def _resolve_scoring_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge provided scoring config with defaults.

    Args:
        config: User scoring configuration dictionary.
    """
    merged = {
        "weights": dict(DEFAULT_SCORING_CONFIG["weights"]),
        "params": dict(DEFAULT_SCORING_CONFIG["params"])
    }

    for section in ["weights", "params"]:
        user_section = (config or {}).get(section, {})
        if not isinstance(user_section, dict):
            continue
        for key, value in user_section.items():
            merged[section][key] = value
    return merged


def compute_score(
    metrics: Dict[str, Any],
    scoring_config: Dict[str, Any] = None
) -> Dict[str, float]:
    """
    Compute per-sample score and factors.

    Args:
        metrics: Per-sample metric dictionary.
        scoring_config: Score config with weights and params.
    """
    cfg = _resolve_scoring_config(scoring_config or {})
    weights = cfg["weights"]
    params = cfg["params"]

    c = 1.0 if int(metrics.get("accuracy", 0)) == 1 else 0.0
    length_tokens = max(0.0, float(metrics.get("response_length_tokens", 0.0)))
    reflection_count = max(0.0, float(metrics.get("reflection_count", 0.0)))
    answer_count = max(0.0, float(metrics.get("answer_count", 0.0)))
    tail_ratio = max(0.0, min(1.0, float(metrics.get("tail_ratio", 1.0))))

    L_ref = _safe_positive(params.get("L_ref"), 256.0)
    tau_d = _safe_positive(params.get("tau_d"), 256.0)
    a_star = float(params.get("a_star", 2.0))
    tau_a = _safe_positive(params.get("tau_a"), 2.0)
    r_star = float(params.get("r_star", 2.0))
    tau_r = _safe_positive(params.get("tau_r"), 2.0)
    rho_star = float(params.get("rho_star", 0.25))
    tau_tail = _safe_positive(params.get("tau_tail"), 0.20)

    length_factor = math.exp(-max(0.0, length_tokens - L_ref) / tau_d)
    count_factor = math.exp(-max(0.0, answer_count - a_star) / tau_a)
    tail_factor = math.exp(-max(0.0, tail_ratio - rho_star) / tau_tail)
    answer_factor = max(0.0, min(1.0, count_factor * tail_factor))
    reflection_factor = math.exp(-abs(reflection_count - r_star) / tau_r)

    w_answer = float(weights.get("answer", 0.3))
    w_length = float(weights.get("length", 0.4))
    w_reflection = float(weights.get("reflection", 0.3))

    score = c
    score *= answer_factor ** w_answer
    score *= length_factor ** w_length
    score *= reflection_factor ** w_reflection
    score = max(0.0, min(1.0, score))

    return {
        "length_factor": length_factor,
        "count_factor": count_factor,
        "tail_factor": tail_factor,
        "answer_factor": answer_factor,
        "reflection_factor": reflection_factor,
        "score_i": score
    }
