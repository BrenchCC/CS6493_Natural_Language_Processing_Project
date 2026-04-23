"""Summarize evaluated run files into CSV reports."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any
from typing import Dict
from typing import Iterable
from typing import List

from evaluation.io_utils import read_jsonl
from infer_exp.config_utils import load_experiment_config


SUMMARY_FIELDS = [
    "run_id",
    "model_alias",
    "model_name",
    "method_name",
    "dataset_name",
    "sample_count",
    "accuracy",
    "avg_response_length_tokens",
    "avg_response_length_chars",
    "avg_score_i",
    "source_file",
]


def summarize_records(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Build summary stats for one evaluated record list."""
    if not records:
        return {
            "run_id": "",
            "model_alias": "",
            "model_name": "",
            "method_name": "",
            "dataset_name": "",
            "sample_count": 0,
            "accuracy": 0.0,
            "avg_response_length_tokens": 0.0,
            "avg_response_length_chars": 0.0,
            "avg_score_i": 0.0,
        }

    return {
        "run_id": records[0].get("run_id", ""),
        "model_alias": records[0].get("model_alias", ""),
        "model_name": records[0].get("model_name", ""),
        "method_name": records[0].get("method_name", ""),
        "dataset_name": records[0].get("dataset_name", ""),
        "sample_count": len(records),
        "accuracy": mean(float(record.get("accuracy", 0)) for record in records),
        "avg_response_length_tokens": mean(float(record.get("response_length_tokens", 0)) for record in records),
        "avg_response_length_chars": mean(float(record.get("response_length_chars", 0)) for record in records),
        "avg_score_i": mean(float(record.get("score_i", 0.0)) for record in records),
    }


def _write_csv(path: Path, rows: Iterable[Dict[str, Any]], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents = True, exist_ok = True)
    with path.open("w", encoding = "utf-8", newline = "") as file:
        writer = csv.DictWriter(file, fieldnames = fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def summarize_all(config_path: str) -> Dict[str, str]:
    """Summarize all evaluated files into aggregate CSV reports."""
    config = load_experiment_config(config_path)
    evaluated_dir = Path(config["run"]["evaluated_dir"])
    summary_dir = Path(config["run"]["summary_dir"])

    aggregate_rows: List[Dict[str, Any]] = []
    metric_rows: List[Dict[str, Any]] = []

    grouped_by_run: dict[tuple[str, str, str], list[Dict[str, Any]]] = defaultdict(list)

    for evaluated_file in sorted(evaluated_dir.glob("*.jsonl")):
        records = read_jsonl(str(evaluated_file))
        file_summary = summarize_records(records)
        file_summary["source_file"] = evaluated_file.name
        aggregate_rows.append(file_summary)
        grouped_by_run[(file_summary["run_id"], file_summary["model_alias"], file_summary["method_name"])].extend(records)

        for metric_name in ["accuracy", "response_length_tokens", "response_length_chars", "score_i"]:
            values = [float(record.get(metric_name, 0.0)) for record in records]
            metric_rows.append(
                {
                    "run_id": file_summary["run_id"],
                    "model_alias": file_summary["model_alias"],
                    "model_name": file_summary["model_name"],
                    "method_name": file_summary["method_name"],
                    "dataset_name": file_summary["dataset_name"],
                    "metric": metric_name,
                    "mean": mean(values) if values else 0.0,
                    "min": min(values) if values else 0.0,
                    "max": max(values) if values else 0.0,
                }
            )

    for (run_id, model_alias, method_name), records in grouped_by_run.items():
        overall_summary = summarize_records(records)
        overall_summary["dataset_name"] = "overall"
        overall_summary["source_file"] = "all"
        overall_summary["run_id"] = run_id
        overall_summary["model_alias"] = model_alias
        overall_summary["method_name"] = method_name
        aggregate_rows.append(overall_summary)

    aggregate_path = summary_dir / "aggregate_scores.csv"
    metrics_path = summary_dir / "single_metric_stats.csv"
    _write_csv(aggregate_path, aggregate_rows, SUMMARY_FIELDS)
    _write_csv(
        metrics_path,
        metric_rows,
        ["run_id", "model_alias", "model_name", "method_name", "dataset_name", "metric", "mean", "min", "max"],
    )
    return {
        "aggregate_scores": str(aggregate_path),
        "single_metric_stats": str(metrics_path),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description = "Summarize evaluated run JSONL files.")
    parser.add_argument("--config", required = True, help = "Path to YAML config.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summarize_all(args.config)


if __name__ == "__main__":
    main()
