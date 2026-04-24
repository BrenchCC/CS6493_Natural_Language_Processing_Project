"""Metric extraction utilities for evaluated records."""

from __future__ import annotations

import math
import re
from typing import Any
from typing import Dict
from typing import Tuple

from .math_grader import math_equal
from .parser import extract_answer
from .parser import strip_string


ANSWER_SIGNAL_PATTERNS = [
    r"\\boxed\{",
    r"final answer is",
    r"the answer is",
    r"answer:",
    r"答案是",
]

DEFAULT_REFLECTION_PATTERNS = [
    r"\bwait\b",
    r"\balternatively\b",
    r"\bhmm\b",
    r"\bbut\b",
    r"\bhowever\b",
    r"\balternative\b",
    r"\banother\b",
    r"\bcheck\b",
    r"\bdouble-check\b",
    r"\boh\b",
    r"\bmaybe\b",
    r"\bverify\b",
    r"\bother\b",
    r"\bagain\b",
    r"\bnow\b",
    r"\bah\b",
    r"\bany\b",
    r"rethink",
    r"review",
    r"double-check",
    r"check again",
    r"let me verify",
    r"反思",
    r"检查",
]


def extract_final_answer(raw_output: str, dataset_name: str = "math500") -> str:
    """Extract the final answer from a model response."""
    return extract_answer(raw_output or "", dataset_name)


def detect_answer_signals(text: str) -> Tuple[int, int]:
    """Count answer cues and return the first cue index."""
    if not text:
        return 0, -1

    matches: list[re.Match[str]] = []
    for pattern in ANSWER_SIGNAL_PATTERNS:
        matches.extend(re.finditer(pattern, text, flags = re.IGNORECASE))

    if not matches:
        return 0, -1

    first_index = min(match.start() for match in matches)
    return len(matches), first_index


def count_reflections(text: str, reflection_patterns: list[str] | None = None) -> int:
    """Count reflective phrases that hint at over-reasoning."""
    if not text:
        return 0

    patterns = reflection_patterns or DEFAULT_REFLECTION_PATTERNS
    count = 0
    for pattern in patterns:
        count += len(re.findall(pattern, text, flags = re.IGNORECASE))
    return count


def normalize_ground_truth(ground_truth: Any, dataset_name: str = "math500") -> str:
    """Normalize ground-truth answers from processed datasets."""
    text = str(ground_truth or "").strip()
    dataset_name = dataset_name.lower()

    if not text:
        return ""
    if dataset_name == "gsm8k" or "####" in text:
        return extract_answer(text, "gsm8k")
    if "boxed" in text or "final answer is" in text.lower():
        return extract_answer(text, "math")
    return strip_string(text)


def _estimate_token_count(text: str) -> int:
    """Estimate token count with a whitespace fallback."""
    stripped = (text or "").strip()
    if not stripped:
        return 0
    return len(stripped.split())


def _tail_ratio(text: str, first_signal_idx: int) -> float:
    """Compute remaining text ratio after the first answer signal."""
    if not text or first_signal_idx < 0 or first_signal_idx >= len(text):
        return 0.0
    tail_chars = len(text[first_signal_idx:])
    return tail_chars / max(len(text), 1)


def collect_metrics(
    raw_output: str,
    ground_truth: Any,
    dataset_name: str = "math500",
    reflection_patterns: list[str] | None = None,
) -> Dict[str, Any]:
    """Collect core evaluation metrics for one response."""
    output_text = raw_output or ""
    final_answer = extract_final_answer(output_text, dataset_name = dataset_name)
    normalized_ground_truth = normalize_ground_truth(ground_truth, dataset_name = dataset_name)
    answer_count, first_answer_token_idx = detect_answer_signals(output_text)
    reflection_count = count_reflections(output_text, reflection_patterns = reflection_patterns)
    accuracy = 1 if math_equal(final_answer, normalized_ground_truth) else 0
    response_length_chars = len(output_text)
    response_length_tokens = _estimate_token_count(output_text)
    tail_ratio = _tail_ratio(output_text, first_answer_token_idx)

    return {
        "final_answer": final_answer,
        "normalized_ground_truth": normalized_ground_truth,
        "accuracy": accuracy,
        "response_length_tokens": response_length_tokens,
        "response_length_chars": response_length_chars,
        "reflection_count": reflection_count,
        "answer_count": answer_count,
        "first_answer_token_idx": first_answer_token_idx,
        "tail_ratio": 0.0 if math.isnan(tail_ratio) else tail_ratio,
    }
