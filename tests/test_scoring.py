"""
Unit tests for score computation.
"""

import os
import sys

# Add project root to Python path
sys.path.append(os.getcwd())

from evaluation.scoring import compute_score


def _base_metrics() -> dict:
    """
    Build a baseline metric dictionary.

    Args:
        None.
    """
    return {
        "accuracy": 1,
        "response_length_tokens": 200,
        "reflection_count": 2,
        "answer_count": 2,
        "tail_ratio": 0.20
    }


def test_score_in_range() -> None:
    """
    Ensure score is always within [0, 1].

    Args:
        None.
    """
    metrics = _base_metrics()
    score_data = compute_score(metrics = metrics)
    assert 0.0 <= score_data["score_i"] <= 1.0


def test_wrong_answer_gate_zero() -> None:
    """
    Ensure wrong answer is strictly gated to zero.

    Args:
        None.
    """
    metrics = _base_metrics()
    metrics["accuracy"] = 0
    score_data = compute_score(metrics = metrics)
    assert score_data["score_i"] == 0.0


def test_answer_count_monotonic_penalty() -> None:
    """
    Ensure larger answer_count beyond a_star decreases score.

    Args:
        None.
    """
    metrics_low = _base_metrics()
    metrics_high = _base_metrics()
    metrics_high["answer_count"] = 6

    low_score = compute_score(metrics = metrics_low)["score_i"]
    high_score = compute_score(metrics = metrics_high)["score_i"]
    assert high_score < low_score


def test_tail_ratio_monotonic_penalty() -> None:
    """
    Ensure larger post-answer tail ratio decreases score.

    Args:
        None.
    """
    metrics_low = _base_metrics()
    metrics_high = _base_metrics()
    metrics_high["tail_ratio"] = 0.90

    low_score = compute_score(metrics = metrics_low)["score_i"]
    high_score = compute_score(metrics = metrics_high)["score_i"]
    assert high_score < low_score


def test_weight_setting_respected() -> None:
    """
    Ensure custom weight config is accepted.

    Args:
        None.
    """
    metrics = _base_metrics()
    score_data = compute_score(
        metrics = metrics,
        scoring_config = {
            "weights": {
                "answer": 0.3,
                "length": 0.4,
                "reflection": 0.3
            }
        }
    )
    assert 0.0 <= score_data["score_i"] <= 1.0
