"""
Summarize evaluated scores into grouped statistics tables.
"""

import os
import sys
import csv
import argparse
import logging
from pathlib import Path
from statistics import mean
from statistics import median
from statistics import mode
from typing import Any
from typing import Dict
from typing import List

# Add project root to Python path
sys.path.append(os.getcwd())

from evaluation.io_utils import read_jsonl
from infer_exp.config_utils import ensure_dir
from infer_exp.config_utils import load_yaml_config


logger = logging.getLogger(__name__)


GROUP_KEYS = ["model_id", "dataset", "method"]
METRIC_COLUMNS = [
    "accuracy",
    "response_length_tokens",
    "response_length_chars",
    "reflection_count",
    "answer_count",
    "tail_ratio",
    "score_i"
]


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Args:
        None.
    """
    parser = argparse.ArgumentParser(description = "Summarize evaluated run results.")
    parser.add_argument(
        "--config",
        type = str,
        required = True,
        help = "Path to YAML config file."
    )
    return parser.parse_args()


def _safe_mode(values: List[float]) -> float:
    """
    Return deterministic mode value.

    Args:
        values: Numeric value list.
    """
    if not values:
        return 0.0
    try:
        return mode(values)
    except Exception:
        return sorted(values)[0]


def _collect_evaluated_files(evaluated_dir: str) -> List[Path]:
    """
    Collect evaluated JSONL files.

    Args:
        evaluated_dir: Evaluated result directory.
    """
    root = Path(evaluated_dir)
    if not root.exists():
        return []
    return sorted(root.glob("*.jsonl"))


def _group_records(records: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Group records by model, dataset, and method.

    Args:
        records: Evaluated record list.
    """
    groups = {}
    for item in records:
        key_values = [str(item.get(key, "")) for key in GROUP_KEYS]
        group_key = "||".join(key_values)
        groups.setdefault(group_key, []).append(item)
    return groups


def summarize_scores(config: Dict[str, Any]) -> Dict[str, str]:
    """
    Build aggregate CSV summaries from evaluated files.

    Args:
        config: Experiment configuration dictionary.
    """
    run_cfg = config.get("run", {})
    evaluated_dir = run_cfg.get("evaluated_dir", "results/evaluated")
    summary_dir = run_cfg.get("summary_dir", "results/summaries")
    ensure_dir(summary_dir)

    all_records = []
    for file_path in _collect_evaluated_files(evaluated_dir):
        all_records.extend(read_jsonl(str(file_path)))

    grouped = _group_records(all_records)

    aggregate_rows = []
    single_metric_rows = []
    for group_key, rows in grouped.items():
        model_id, dataset, method_name = group_key.split("||")
        scores = [float(item.get("score_i", 0.0)) for item in rows]

        aggregate_rows.append(
            {
                "model_id": model_id,
                "dataset": dataset,
                "method": method_name,
                "num_samples": len(rows),
                "score_mean": mean(scores) if scores else 0.0,
                "score_median": median(scores) if scores else 0.0,
                "score_mode": _safe_mode(scores)
            }
        )

        metric_row = {
            "model_id": model_id,
            "dataset": dataset,
            "method": method_name,
            "num_samples": len(rows)
        }
        for metric_name in METRIC_COLUMNS:
            values = [float(item.get(metric_name, 0.0)) for item in rows]
            metric_row[f"{metric_name}_mean"] = mean(values) if values else 0.0
        single_metric_rows.append(metric_row)

    aggregate_path = Path(summary_dir) / "aggregate_scores.csv"
    with aggregate_path.open(mode = "w", encoding = "utf-8", newline = "") as file:
        writer = csv.DictWriter(
            file,
            fieldnames = [
                "model_id",
                "dataset",
                "method",
                "num_samples",
                "score_mean",
                "score_median",
                "score_mode"
            ]
        )
        writer.writeheader()
        writer.writerows(sorted(aggregate_rows, key = lambda row: (row["model_id"], row["dataset"], row["method"])))

    single_metric_path = Path(summary_dir) / "single_metric_stats.csv"
    single_fields = ["model_id", "dataset", "method", "num_samples"] + [
        f"{metric_name}_mean" for metric_name in METRIC_COLUMNS
    ]
    with single_metric_path.open(mode = "w", encoding = "utf-8", newline = "") as file:
        writer = csv.DictWriter(file, fieldnames = single_fields)
        writer.writeheader()
        writer.writerows(sorted(single_metric_rows, key = lambda row: (row["model_id"], row["dataset"], row["method"])))

    logger.info("Saved aggregate summary to %s", str(aggregate_path))
    logger.info("Saved metric summary to %s", str(single_metric_path))

    return {
        "aggregate_scores": str(aggregate_path),
        "single_metric_stats": str(single_metric_path)
    }


def main() -> None:
    """
    Run CLI entrypoint.

    Args:
        None.
    """
    args = parse_args()
    config = load_yaml_config(args.config)
    summarize_scores(config)


if __name__ == "__main__":
    logging.basicConfig(
        level = logging.INFO,
        format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers = [logging.StreamHandler()]
    )
    main()
