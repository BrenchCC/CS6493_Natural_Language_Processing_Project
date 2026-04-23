"""Composite score computation for evaluated records."""

from __future__ import annotations

import math
from typing import Any
from typing import Dict


DEFAULT_SCORING_CONFIG: Dict[str, Any] = {
    "weights": {
        "answer": 0.3,
        "length": 0.4,
        "reflection": 0.3,
    },
    "params": {
        "a_star": 2,
        "tau_a": 2.0,
        "r_star": 1,
        "tau_r": 2.0,
        "rho_star": 0.2,
        "tau_tail": 0.2,
        "L_ref": 200,
        "tau_d": 200.0,
    },
}


def _merge_scoring_config(scoring_config: Dict[str, Any] | None) -> Dict[str, Any]:
    merged = {
        "weights": dict(DEFAULT_SCORING_CONFIG["weights"]),
        "params": dict(DEFAULT_SCORING_CONFIG["params"]),
    }
    if not scoring_config:
        return merged

    for section in ("weights", "params"):
        if section in scoring_config and isinstance(scoring_config[section], dict):
            merged[section].update(scoring_config[section])
    return merged


def compute_score(metrics: Dict[str, Any], scoring_config: Dict[str, Any] | None = None) -> Dict[str, float]:
    """Compute a bounded score in `[0, 1]`."""
    config = _merge_scoring_config(scoring_config)
    weights = config["weights"]
    params = config["params"]

    accuracy = float(metrics.get("accuracy", 0))
    response_length = float(metrics.get("response_length_tokens", metrics.get("response_length_chars", 0)))
    reflection_count = float(metrics.get("reflection_count", 0))
    answer_count = float(metrics.get("answer_count", 0))
    tail_ratio = float(metrics.get("tail_ratio", 0.0))

    length_factor = math.exp(-max(0.0, response_length - float(params["L_ref"])) / max(float(params["tau_d"]), 1e-8))
    count_factor = math.exp(-max(0.0, answer_count - float(params["a_star"])) / max(float(params["tau_a"]), 1e-8))
    tail_factor = math.exp(-max(0.0, tail_ratio - float(params["rho_star"])) / max(float(params["tau_tail"]), 1e-8))
    answer_factor = count_factor * tail_factor
    reflection_factor = math.exp(-abs(reflection_count - float(params["r_star"])) / max(float(params["tau_r"]), 1e-8))

    score_i = accuracy * (answer_factor ** float(weights["answer"])) * (length_factor ** float(weights["length"])) * (reflection_factor ** float(weights["reflection"]))
    score_i = max(0.0, min(1.0, score_i))

    return {
        "length_factor": length_factor,
        "count_factor": count_factor,
        "tail_factor": tail_factor,
        "answer_factor": answer_factor,
        "reflection_factor": reflection_factor,
        "score_i": score_i,
    }
