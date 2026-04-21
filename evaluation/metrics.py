"""
Metric extraction utilities for math reasoning outputs.
"""

import re
from fractions import Fraction
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple


REFLECTION_PATTERN = re.compile(
    r"\b(rethink|reconsider|double-check|check again|verify|verification|"
    r"mistake|error|correction|corrected|revise|on second thought)\b",
    re.IGNORECASE
)

BOXED_PATTERN = re.compile(r"\\boxed\s*\{([^{}]+)\}", re.IGNORECASE)
FINAL_ANSWER_PATTERN = re.compile(
    r"(?:final answer\s*(?:is|:)|answer\s*:?)\s*([^\n\.]+)",
    re.IGNORECASE
)
NUMBER_PATTERN = re.compile(r"[-+]?\d+(?:\.\d+)?(?:/\d+)?")
ANSWER_SIGNAL_PATTERNS = [
    re.compile(r"\\boxed\s*\{[^{}]+\}", re.IGNORECASE),
    re.compile(r"final answer\s*(?:is|:)", re.IGNORECASE),
    re.compile(r"answer\s*:", re.IGNORECASE)
]


def tokenize_text(text: str) -> List[str]:
    """
    Split response text into whitespace tokens.

    Args:
        text: Model response text.
    """
    return text.split()


def extract_final_answer(text: str) -> str:
    """
    Extract final answer string from a model response.

    Args:
        text: Model response text.
    """
    boxed = BOXED_PATTERN.findall(text)
    if boxed:
        return boxed[-1].strip()

    answer_match = FINAL_ANSWER_PATTERN.findall(text)
    if answer_match:
        return answer_match[-1].strip()

    numbers = NUMBER_PATTERN.findall(text)
    if numbers:
        return numbers[-1].strip()
    return text.strip()


def normalize_answer(answer: str) -> str:
    """
    Normalize answer text for comparison.

    Args:
        answer: Raw answer text.
    """
    cleaned = answer.strip().lower()
    cleaned = cleaned.strip("$")
    cleaned = cleaned.replace(",", "")
    cleaned = re.sub(r"\s+", "", cleaned)
    cleaned = cleaned.rstrip(".")
    return cleaned


def _to_float(answer: str) -> Optional[float]:
    """
    Convert normalized answer to float when possible.

    Args:
        answer: Normalized answer text.
    """
    try:
        if "/" in answer and not answer.startswith("http"):
            return float(Fraction(answer))
        return float(answer)
    except Exception:
        return None


def are_answers_equivalent(prediction: str, reference: str) -> bool:
    """
    Check whether prediction and reference are equivalent.

    Args:
        prediction: Predicted answer text.
        reference: Ground-truth answer text.
    """
    pred_norm = normalize_answer(prediction)
    ref_norm = normalize_answer(reference)

    if pred_norm == ref_norm:
        return True

    pred_float = _to_float(pred_norm)
    ref_float = _to_float(ref_norm)
    if pred_float is None or ref_float is None:
        return False

    return abs(pred_float - ref_float) <= 1e-6


def count_reflection_terms(text: str) -> int:
    """
    Count reflection keyword hits in response text.

    Args:
        text: Model response text.
    """
    return len(REFLECTION_PATTERN.findall(text))


def detect_answer_signals(text: str) -> Tuple[int, int]:
    """
    Count answer signals and locate first signal char index.

    Args:
        text: Model response text.
    """
    spans = []
    for pattern in ANSWER_SIGNAL_PATTERNS:
        for match in pattern.finditer(text):
            spans.append((match.start(), match.end()))

    spans.sort(key = lambda pair: pair[0])
    deduplicated = []
    for start, end in spans:
        if not deduplicated:
            deduplicated.append((start, end))
            continue
        prev_start, prev_end = deduplicated[-1]
        if start < prev_end:
            if end > prev_end:
                deduplicated[-1] = (prev_start, end)
            continue
        deduplicated.append((start, end))

    answer_count = len(deduplicated)
    first_char_idx = deduplicated[0][0] if deduplicated else -1
    return answer_count, first_char_idx


def compute_tail_ratio(
    text: str,
    first_answer_char_idx: int
) -> Tuple[int, float]:
    """
    Compute first answer token index and post-answer token ratio.

    Args:
        text: Model response text.
        first_answer_char_idx: Char index of first answer signal.
    """
    tokens = tokenize_text(text)
    total_tokens = max(1, len(tokens))

    if first_answer_char_idx < 0:
        return -1, 1.0

    prefix = text[:first_answer_char_idx]
    first_token_idx = len(prefix.split())
    first_token_idx = min(first_token_idx, total_tokens - 1)
    tokens_after_first = max(0, total_tokens - first_token_idx - 1)
    tail_ratio = tokens_after_first / total_tokens
    return first_token_idx, tail_ratio


def collect_metrics(
    raw_output: str,
    ground_truth: str,
    final_answer: Optional[str] = None
) -> Dict[str, Any]:
    """
    Compute per-sample metrics used in evaluation and scoring.

    Args:
        raw_output: Full generated response text.
        ground_truth: Ground-truth answer text.
        final_answer: Optional pre-extracted answer.
    """
    predicted = final_answer if final_answer is not None else extract_final_answer(raw_output)

    answer_count, first_char_idx = detect_answer_signals(raw_output)
    first_answer_token_idx, tail_ratio = compute_tail_ratio(
        text = raw_output,
        first_answer_char_idx = first_char_idx
    )

    tokens = tokenize_text(raw_output)
    response_length_tokens = len(tokens)
    response_length_chars = len(raw_output)
    reflection_count = count_reflection_terms(raw_output)
    accuracy = int(are_answers_equivalent(predicted, ground_truth))

    return {
        "final_answer": predicted,
        "accuracy": accuracy,
        "response_length_tokens": response_length_tokens,
        "response_length_chars": response_length_chars,
        "reflection_count": reflection_count,
        "answer_count": answer_count,
        "first_answer_token_idx": first_answer_token_idx,
        "tail_ratio": tail_ratio
    }
