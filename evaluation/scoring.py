"""Composite score computation for evaluated records."""

from __future__ import annotations

import math
from typing import Any
from typing import Dict


DEFAULT_SCORING_CONFIG: Dict[str, Any] = {
    "weights": {
        "answer": 0.3,
        "length": 0.5,
        "reflection": 0.2,
    },
    "params": {
        "length_ref": 1024,
        "tau_length": 512.0,
        "answer_count_ref": 1,
        "tau_answer_count": 1.0,
        "tail_ratio_ref": 0.2,
        "tau_tail_ratio": 0.2,
        "reflection_count_ref": 1,
        "tau_reflection": 2.0,
    },
}

LEGACY_PARAM_ALIASES = {
    "L_ref": "length_ref",
    "tau_d": "tau_length",
    "a_star": "answer_count_ref",
    "tau_a": "tau_answer_count",
    "rho_star": "tail_ratio_ref",
    "tau_tail": "tau_tail_ratio",
    "r_star": "reflection_count_ref",
    "tau_r": "tau_reflection",
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
            section_values = dict(scoring_config[section])
            if section == "params":
                for legacy_key, new_key in LEGACY_PARAM_ALIASES.items():
                    if legacy_key in section_values and new_key not in section_values:
                        section_values[new_key] = section_values[legacy_key]
            merged[section].update(section_values)

    for legacy_key, new_key in LEGACY_PARAM_ALIASES.items():
        if legacy_key in merged["params"]:
            merged["params"][new_key] = merged["params"].get(new_key, merged["params"][legacy_key])

    return merged


def _require_metric(metrics: Dict[str, Any], field_name: str) -> float:
    if field_name not in metrics:
        raise ValueError(f"Missing required metric field: {field_name}")
    return float(metrics[field_name])


def _resolve_response_length(metrics: Dict[str, Any]) -> float:
    if "total_response_length_tokens" in metrics:
        return float(metrics["total_response_length_tokens"])
    if "response_length_tokens" in metrics:
        return float(metrics["response_length_tokens"])
    if "total_response_length_chars" in metrics:
        return float(metrics["total_response_length_chars"])
    if "response_length_chars" in metrics:
        return float(metrics["response_length_chars"])
    raise ValueError("Missing required metric field: response_length")


def _validate_inputs(metrics: Dict[str, Any], config: Dict[str, Any]) -> tuple[float, float, float, float, float]:
    accuracy = _require_metric(metrics, "accuracy")
    response_length = _resolve_response_length(metrics)
    reflection_count = _require_metric(metrics, "reflection_count")
    answer_count = _require_metric(metrics, "answer_count")
    tail_ratio = _require_metric(metrics, "tail_ratio")

    params = config["params"]
    weights = config["weights"]

    if accuracy not in {0.0, 1.0}:
        raise ValueError("accuracy must be 0 or 1")
    if response_length < 0:
        raise ValueError("response_length must be non-negative")
    if answer_count < 0:
        raise ValueError("answer_count must be non-negative")
    if reflection_count < 0:
        raise ValueError("reflection_count must be non-negative")
    if not 0.0 <= tail_ratio <= 1.0:
        raise ValueError("tail_ratio must be within [0, 1]")

    for param_name in ("tau_length", "tau_answer_count", "tau_tail_ratio", "tau_reflection"):
        if float(params[param_name]) <= 0:
            raise ValueError(f"{param_name} must be positive")

    weight_sum = float(weights["answer"]) + float(weights["length"]) + float(weights["reflection"])
    if not math.isclose(weight_sum, 1.0, rel_tol = 1e-9, abs_tol = 1e-9):
        raise ValueError("weight_length + weight_answer + weight_reflection must equal 1.0")

    return accuracy, response_length, reflection_count, answer_count, tail_ratio


def compute_score(metrics: Dict[str, Any], scoring_config: Dict[str, Any] | None = None) -> Dict[str, float]:
    """Compute a bounded score in `[0, 1]`."""
    config = _merge_scoring_config(scoring_config)
    weights = config["weights"]
    params = config["params"]

    accuracy, response_length, reflection_count, answer_count, tail_ratio = _validate_inputs(metrics, config)

    length_factor = math.exp(-max(0.0, response_length - float(params["length_ref"])) / float(params["tau_length"]))
    count_factor = math.exp(-max(0.0, answer_count - float(params["answer_count_ref"])) / float(params["tau_answer_count"]))
    if answer_count < 2:
        tail_factor = 1.0
    else:
        tail_factor = math.exp(-max(0.0, tail_ratio - float(params["tail_ratio_ref"])) / float(params["tau_tail_ratio"]))
    answer_factor = count_factor * tail_factor
    reflection_factor = math.exp(-max(0.0, reflection_count - float(params["reflection_count_ref"])) / float(params["tau_reflection"]))

    efficiency_i = (
        (answer_factor ** float(weights["answer"]))
        * (length_factor ** float(weights["length"]))
        * (reflection_factor ** float(weights["reflection"]))
    )
    efficiency_i = max(0.0, min(1.0, efficiency_i))
    score_i = accuracy * efficiency_i
    score_i = max(0.0, min(1.0, score_i))

    return {
        "efficiency_i": efficiency_i,
        "length_factor": length_factor,
        "count_factor": count_factor,
        "tail_factor": tail_factor,
        "answer_factor": answer_factor,
        "reflection_factor": reflection_factor,
        "score_i": score_i,
    }
