"""Evaluate raw experiment outputs into scored JSONL files."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List

from evaluation.io_utils import read_jsonl
from evaluation.io_utils import write_jsonl
from evaluation.metrics import collect_metrics
from evaluation.scoring import compute_score
from infer_exp.config_utils import load_experiment_config
from tqdm import tqdm


def build_total_output(record: Dict[str, Any], raw_output: str) -> str:
    """
    Build the full generated-output text for cost-sensitive length metrics.

    Args:
        record: Raw or evaluated experiment record.
        raw_output: Final response text used for answer extraction.
    """
    intermediate_outputs = record.get("intermediate_outputs")
    if not isinstance(intermediate_outputs, list) or not intermediate_outputs:
        return raw_output

    method_name = str(record.get("method_name", ""))
    if method_name == "tir":
        return raw_output

    parts: List[str] = []
    for item in intermediate_outputs:
        if not isinstance(item, dict):
            continue
        for field_name in ("response", "raw_response"):
            text = item.get(field_name)
            if isinstance(text, str) and text.strip():
                parts.append(text)
                break

    return "\n".join(parts).strip() or raw_output


def extract_api_usage_metrics(record: Dict[str, Any]) -> Dict[str, Any]:
    """Extract saved API usage metadata into top-level numeric metrics.

    Args:
        record: Raw or evaluated experiment record.
    """
    metadata = record.get("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}
    api_usage = metadata.get("api_usage", {})
    if not isinstance(api_usage, dict):
        api_usage = {}

    return {
        "api_call_count": api_usage.get("api_call_count", 0),
        "api_prompt_tokens": api_usage.get("api_prompt_tokens", 0.0),
        "api_completion_tokens": api_usage.get("api_completion_tokens", 0.0),
        "api_total_tokens": api_usage.get("api_total_tokens", 0.0),
        "api_reasoning_tokens": api_usage.get("api_reasoning_tokens", 0.0),
        "api_estimated_reasoning_tokens": api_usage.get("api_estimated_reasoning_tokens", 0.0),
        "api_reasoning_content_chars": api_usage.get("api_reasoning_content_chars", 0.0),
    }


def apply_api_completion_total(metrics: Dict[str, Any], api_usage_metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Use provider completion tokens as total generated length when available.

    Args:
        metrics: Metrics computed from visible response text.
        api_usage_metrics: Top-level API usage metrics extracted from metadata.
    """
    completion_tokens = float(api_usage_metrics.get("api_completion_tokens") or 0.0)
    if completion_tokens <= 0:
        return metrics

    updated_metrics = dict(metrics)
    updated_metrics["total_response_length_tokens"] = completion_tokens
    return updated_metrics


def evaluate_record(record: Dict[str, Any], scoring_config: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Evaluate one raw record and append metric fields."""
    dataset_name = str(record.get("dataset_name", record.get("dataset", "math500")))
    raw_output = str(record.get("final_response") or record.get("raw_response") or "")
    total_output = build_total_output(record, raw_output = raw_output)
    ground_truth = record.get("gold_answer", "")
    api_usage_metrics = extract_api_usage_metrics(record = record)

    metrics = collect_metrics(
        raw_output = raw_output,
        ground_truth = ground_truth,
        dataset_name = dataset_name,
        reflection_patterns = (scoring_config or {}).get("reflection_patterns"),
        total_output = total_output,
    )
    metrics = apply_api_completion_total(metrics = metrics, api_usage_metrics = api_usage_metrics)
    score_data = compute_score(metrics = metrics, scoring_config = scoring_config)

    evaluated = dict(record)
    evaluated["parsed_prediction"] = metrics["final_answer"]
    evaluated.update(metrics)
    evaluated.update(score_data)
    evaluated.update(api_usage_metrics)
    return evaluated


def evaluate_raw_file(
    raw_path: str | Path,
    evaluated_path: str | Path,
    scoring_config: Dict[str, Any] | None = None,
    num_workers: int = 1,
    show_progress: bool = True,
) -> List[Dict[str, Any]]:
    """Evaluate one raw JSONL file and write its evaluated counterpart."""
    records = read_jsonl(str(raw_path))
    progress_desc = f"Eval {Path(raw_path).stem}"
    if num_workers <= 1 or len(records) <= 1:
        evaluated_records = [
            evaluate_record(record, scoring_config = scoring_config)
            for record in tqdm(
                records,
                total = len(records),
                desc = progress_desc,
                dynamic_ncols = True,
                disable = not show_progress,
            )
        ]
    else:
        with ThreadPoolExecutor(max_workers = num_workers) as executor:
            evaluated_records = list(
                tqdm(
                    executor.map(
                        lambda record: evaluate_record(record, scoring_config = scoring_config),
                        records,
                    ),
                    total = len(records),
                    desc = progress_desc,
                    dynamic_ncols = True,
                    disable = not show_progress,
                )
            )
    write_jsonl(str(evaluated_path), evaluated_records)
    return evaluated_records


def evaluate_all_runs(config_path: str) -> List[str]:
    """Evaluate every raw run declared by the current config."""
    config = load_experiment_config(config_path)
    output_dir = Path(config["run"]["output_dir"])
    evaluated_dir = Path(config["run"]["evaluated_dir"])
    scoring_config = config.get("scoring", {})
    num_workers = int(config.get("run", {}).get("eval_num_workers", config.get("run", {}).get("num_workers", 1)))
    written_files: List[str] = []

    for raw_file in sorted(output_dir.glob("*.jsonl")):
        target_path = evaluated_dir / raw_file.name
        evaluate_raw_file(raw_file, target_path, scoring_config = scoring_config, num_workers = num_workers)
        written_files.append(str(target_path))

    return written_files


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description = "Evaluate raw run JSONL files.")
    parser.add_argument("--config", required = True, help = "Path to YAML config.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    evaluate_all_runs(args.config)


if __name__ == "__main__":
    main()
