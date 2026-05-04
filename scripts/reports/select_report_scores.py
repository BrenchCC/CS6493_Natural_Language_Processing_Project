"""Select one report row per model/method/dataset and model/method."""

from __future__ import annotations

import csv
import argparse
from pathlib import Path
from typing import Dict
from typing import List
from typing import Tuple


METHODS = [
    "cot_zero",
    "cot_few_shot",
    "self_refine",
    "self_consistency",
    "plan_solve",
    "tir",
]

HIDDEN_OUTPUT_FIELDS = {
    "run_id",
    "source_file",
    "avg_api_call_count",
    "avg_api_prompt_tokens",
    "avg_api_completion_tokens",
    "avg_api_total_tokens",
    "avg_api_reasoning_tokens",
    "avg_api_estimated_reasoning_tokens",
    "avg_api_reasoning_content_chars",
}
USAGE_REQUIRED_METHODS = {"plan_solve", "tir"}

MODEL_ORDER = {
    "DeepSeek-R1-Distill-Qwen-1.5B": 0,
    "Qwen2.5-Math-1.5B-Instruct": 1,
}

DATASET_ORDER = {
    "math500": 0,
    "gsm8k": 1,
    "aime2024": 2,
}


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description = "Select report score rows from aggregate_scores.csv.")
    parser.add_argument(
        "--aggregate",
        action = "append",
        default = None,
        help = "Input aggregate score CSV. Can be passed multiple times.",
    )
    parser.add_argument(
        "--dataset-output",
        default = "results/summaries/report_selected_dataset_scores.csv",
        help = "Output CSV for dataset rows.",
    )
    parser.add_argument(
        "--overall-output",
        default = "results/summaries/report_selected_overall_scores.csv",
        help = "Output CSV for overall rows.",
    )
    return parser.parse_args()


def _score_key(row: Dict[str, str]) -> Tuple[float, float, float, str]:
    """Return sort key for selecting the best row.

    Args:
        row: One aggregate CSV row.
    """
    return (
        float(row.get("joint_score") or 0.0),
        float(row.get("accuracy") or 0.0),
        -float(row.get("avg_total_response_length_tokens") or 0.0),
        str(row.get("run_id") or ""),
    )


def _has_usage(row: Dict[str, str]) -> bool:
    """Return whether a row has recorded API completion usage.

    Args:
        row: One aggregate CSV row.
    """
    return float(row.get("avg_api_completion_tokens") or 0.0) > 0.0


def _select_best_row(rows: List[Dict[str, str]]) -> Dict[str, str]:
    """Select the report row for one model/method grouping.

    Args:
        rows: Candidate aggregate CSV rows for one grouping.
    """
    if not rows:
        raise ValueError("Cannot select from an empty row list.")

    method_name = rows[0].get("method_name", "")
    candidate_rows = rows
    if method_name in USAGE_REQUIRED_METHODS:
        usage_rows = [row for row in rows if _has_usage(row)]
        if usage_rows:
            candidate_rows = usage_rows
    return max(candidate_rows, key = _score_key)


def _write_csv(path: Path, rows: List[Dict[str, str]], fieldnames: List[str]) -> None:
    """Write selected rows to CSV.

    Args:
        path: Output CSV path.
        rows: Selected rows to write.
        fieldnames: CSV field order.
    """
    path.parent.mkdir(parents = True, exist_ok = True)
    with path.open("w", encoding = "utf-8", newline = "") as file:
        writer = csv.DictWriter(file, fieldnames = fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def select_rows(rows: List[Dict[str, str]]) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    """Select highest-joint rows for dataset and overall tables.

    Args:
        rows: Aggregate CSV rows.
    """
    method_order = {method: index for index, method in enumerate(METHODS)}
    filtered_rows = [
        row
        for row in rows
        if row.get("method_name") in method_order and row.get("model_alias") in MODEL_ORDER
    ]

    dataset_candidates: Dict[Tuple[str, str, str], List[Dict[str, str]]] = {}
    overall_candidates: Dict[Tuple[str, str], List[Dict[str, str]]] = {}

    for row in filtered_rows:
        dataset_name = row.get("dataset_name", "")
        if dataset_name == "overall":
            key = (row["model_alias"], row["method_name"])
            overall_candidates.setdefault(key, []).append(row)
        elif dataset_name in DATASET_ORDER:
            key = (row["model_alias"], row["method_name"], dataset_name)
            dataset_candidates.setdefault(key, []).append(row)

    selected_dataset = {
        key: _select_best_row(rows)
        for key, rows in dataset_candidates.items()
    }
    selected_overall = {
        key: _select_best_row(rows)
        for key, rows in overall_candidates.items()
    }

    dataset_rows = sorted(
        selected_dataset.values(),
        key = lambda row: (
            MODEL_ORDER[row["model_alias"]],
            method_order[row["method_name"]],
            DATASET_ORDER[row["dataset_name"]],
        ),
    )
    overall_rows = sorted(
        selected_overall.values(),
        key = lambda row: (MODEL_ORDER[row["model_alias"]], method_order[row["method_name"]]),
    )
    return dataset_rows, overall_rows


def main() -> None:
    """Select report rows and write output CSV files."""
    args = parse_args()
    aggregate_paths = args.aggregate or ["results/summaries/aggregate_scores.csv"]
    rows: List[Dict[str, str]] = []
    fieldnames: List[str] = []
    for aggregate_path_text in aggregate_paths:
        aggregate_path = Path(aggregate_path_text)
        with aggregate_path.open("r", encoding = "utf-8", newline = "") as file:
            reader = csv.DictReader(file)
            if not fieldnames:
                fieldnames = list(reader.fieldnames or [])
            rows.extend(list(reader))

    if not rows:
        raise ValueError(f"No rows found in {aggregate_path}.")

    dataset_rows, overall_rows = select_rows(rows = rows)
    if not fieldnames:
        fieldnames = list(rows[0].keys())
    output_fieldnames = [fieldname for fieldname in fieldnames if fieldname not in HIDDEN_OUTPUT_FIELDS]
    dataset_rows = [
        {fieldname: row.get(fieldname, "") for fieldname in output_fieldnames}
        for row in dataset_rows
    ]
    overall_rows = [
        {fieldname: row.get(fieldname, "") for fieldname in output_fieldnames}
        for row in overall_rows
    ]
    _write_csv(Path(args.dataset_output), rows = dataset_rows, fieldnames = output_fieldnames)
    _write_csv(Path(args.overall_output), rows = overall_rows, fieldnames = output_fieldnames)

    print(f"dataset_rows={len(dataset_rows)}")
    print(f"overall_rows={len(overall_rows)}")


if __name__ == "__main__":
    main()
