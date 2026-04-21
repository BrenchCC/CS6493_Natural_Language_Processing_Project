"""
Unit tests for response metric extraction.
"""

import os
import sys

# Add project root to Python path
sys.path.append(os.getcwd())

from evaluation.metrics import collect_metrics
from evaluation.metrics import detect_answer_signals
from evaluation.metrics import extract_final_answer


def test_extract_final_answer_boxed() -> None:
    """
    Ensure boxed answer extraction works.

    Args:
        None.
    """
    text = "Reasoning... final is \\boxed{42}."
    assert extract_final_answer(text) == "42"


def test_answer_signal_detection() -> None:
    """
    Ensure answer_count and first signal detection works.

    Args:
        None.
    """
    text = "Answer: 3. Then rethink. Final answer is \\boxed{3}."
    count, first_idx = detect_answer_signals(text)
    assert count >= 2
    assert first_idx >= 0


def test_collect_metrics_fields() -> None:
    """
    Ensure required fields exist in collected metrics.

    Args:
        None.
    """
    raw = "Reasoning. Final answer is \\boxed{7}."
    metrics = collect_metrics(raw_output = raw, ground_truth = "7")

    required_keys = [
        "final_answer",
        "accuracy",
        "response_length_tokens",
        "response_length_chars",
        "reflection_count",
        "answer_count",
        "first_answer_token_idx",
        "tail_ratio"
    ]
    for key in required_keys:
        assert key in metrics
