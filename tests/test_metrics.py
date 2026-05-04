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
from evaluation.metrics import _estimate_token_count
from evaluation.evaluate_runs import evaluate_record


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
        "total_response_length_tokens",
        "total_response_length_chars",
        "reflection_count",
        "answer_count",
        "first_answer_token_idx",
        "tail_ratio"
    ]
    for key in required_keys:
        assert key in metrics


def test_collect_metrics_total_length_fields() -> None:
    """
    Ensure total response length can include intermediate generations.

    Args:
        None.
    """
    raw = "Final answer is \\boxed{7}."
    total = "Plan first.\n" + raw
    metrics = collect_metrics(raw_output = raw, ground_truth = "7", total_output = total)

    assert metrics["total_response_length_tokens"] > metrics["response_length_tokens"]
    assert metrics["total_response_length_chars"] > metrics["response_length_chars"]


def test_token_estimate_uses_character_and_word_rules() -> None:
    """
    Ensure token estimates follow the configured approximation rules.

    Args:
        None.
    """
    assert _estimate_token_count("a" * 40) == 10
    assert _estimate_token_count(" ".join(["word"] * 75)) == 100


def test_api_completion_tokens_override_total_generated_length() -> None:
    """
    Ensure API completion tokens drive total generated length when usage is saved.

    Args:
        None.
    """
    record = {
        "dataset_name": "math500",
        "gold_answer": "7",
        "final_response": "Final Answer: \\boxed{7}",
        "metadata": {
            "api_usage": {
                "api_completion_tokens": 1500,
            }
        },
    }

    evaluated = evaluate_record(record = record)

    assert evaluated["response_length_tokens"] < 1500
    assert evaluated["total_response_length_tokens"] == 1500
    assert evaluated["length_factor"] < 1.0
