"""Recalculate evaluated records and optionally overwrite files in place."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any
from typing import Dict
from typing import Iterable
from typing import List

from evaluation.io_utils import read_jsonl
from evaluation.io_utils import write_jsonl
from evaluation.evaluate_runs import build_total_output
from evaluation.evaluate_runs import extract_api_usage_metrics
from evaluation.evaluate_runs import apply_api_completion_total
from evaluation.metrics import collect_metrics
from evaluation.scoring import compute_score
from evaluation.summarize_scores import summarize_all
from evaluation.summarize_scores import summarize_records
from infer_exp.config_utils import get_model_settings
from infer_exp.config_utils import load_experiment_config


def _resolve_scoring_config(config_path: str | None) -> Dict[str, Any] | None:
    """Load scoring config from YAML when provided."""
    if not config_path:
        return None
    config = load_experiment_config(config_path)
    return config.get("scoring", {})


def _iter_selected_records(records: List[Dict[str, Any]], sample_ids: set[str]) -> Iterable[Dict[str, Any]]:
    """Filter records by sample ids when the user provides them."""
    if not sample_ids:
        yield from records
        return

    for record in records:
        if str(record.get("sample_id", "")) in sample_ids:
            yield record


def _recalculate_record(record: Dict[str, Any], scoring_config: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Recompute metrics and score fields for one evaluated record."""
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

    updated = dict(record)
    updated["parsed_prediction"] = metrics["final_answer"]
    updated.update(metrics)
    updated.update(score_data)
    updated.update(api_usage_metrics)
    return updated


def recalculate_file(
    evaluated_path: str,
    scoring_config: Dict[str, Any] | None = None,
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Recalculate one evaluated file and return updated records plus diff rows."""
    records = read_jsonl(evaluated_path)
    updated_records: List[Dict[str, Any]] = []
    rows: List[Dict[str, Any]] = []

    for record in records:
        updated = _recalculate_record(record, scoring_config = scoring_config)
        updated_records.append(updated)
        rows.append(
            {
                "sample_id": updated.get("sample_id", ""),
                "dataset_name": updated.get("dataset_name", ""),
                # accuracy: 题目是否答对，通常为 0 或 1。
                "accuracy": updated.get("accuracy", 0),
                # response_length_tokens: 回复长度（token 数），用于长度惩罚项。
                "response_length_tokens": updated.get("response_length_tokens", 0),
                # total_response_length_tokens: Full multi-pass or multi-sample generated length for length penalty.
                "total_response_length_tokens": updated.get("total_response_length_tokens", 0),
                # reflection_count: 反思/复查类语句次数，用于 reflection 惩罚项。
                "reflection_count": updated.get("reflection_count", 0),
                # answer_count: 明显答案信号出现次数，用于 answer 惩罚项。
                "answer_count": updated.get("answer_count", 0),
                # tail_ratio: 第一次答案信号之后剩余文本占比，用于答案拖尾惩罚项。
                "tail_ratio": updated.get("tail_ratio", 0.0),
                "old_score_i": record.get("score_i", None),
                "length_factor": updated.get("length_factor", 0.0),
                "count_factor": updated.get("count_factor", 0.0),
                "tail_factor": updated.get("tail_factor", 0.0),
                "answer_factor": updated.get("answer_factor", 0.0),
                "reflection_factor": updated.get("reflection_factor", 0.0),
                "new_score_i": updated.get("score_i", 0.0),
                "score_diff": None if record.get("score_i") is None else float(updated.get("score_i", 0.0)) - float(record.get("score_i", 0.0)),
                "old_reflection_count": record.get("reflection_count", None),
                "new_reflection_count": updated.get("reflection_count", 0),
            }
        )

    return updated_records, rows


def _build_summary(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Build aggregate statistics for recalculated rows."""
    if not rows:
        return {
            "avg_old_score_i": None,
            "avg_new_score_i": None,
            "avg_score_diff": None,
            "max_abs_score_diff": 0.0,
            "avg_old_reflection_count": None,
            "avg_new_reflection_count": None,
        }

    old_scores = [float(row["old_score_i"]) for row in rows if row["old_score_i"] is not None]
    new_scores = [float(row["new_score_i"]) for row in rows]
    diffs = [float(row["score_diff"]) for row in rows if row["score_diff"] is not None]
    old_reflections = [float(row["old_reflection_count"]) for row in rows if row["old_reflection_count"] is not None]
    new_reflections = [float(row["new_reflection_count"]) for row in rows]
    return {
        "avg_old_score_i": mean(old_scores) if old_scores else None,
        "avg_new_score_i": mean(new_scores) if new_scores else None,
        "avg_score_diff": mean(diffs) if diffs else None,
        "max_abs_score_diff": max((abs(diff) for diff in diffs), default = 0.0),
        "avg_old_reflection_count": mean(old_reflections) if old_reflections else None,
        "avg_new_reflection_count": mean(new_reflections) if new_reflections else None,
    }


def _print_results(rows: List[Dict[str, Any]], evaluated_path: str, mean_only: bool = False) -> None:
    """Print per-sample recalculation results and a short summary."""
    print(f"# evaluated_file: {Path(evaluated_path).resolve()}")
    print(f"# sample_count: {len(rows)}")

    if not mean_only:
        for row in rows:
            print(json.dumps(row, ensure_ascii = False))

    print("# summary")
    print(json.dumps(_build_summary(rows), ensure_ascii = False))


def _iter_input_files(input_path: str) -> List[Path]:
    """Resolve a file or directory input into evaluated JSONL file paths."""
    path = Path(input_path)
    if path.is_file():
        return [path]
    if path.is_dir():
        return sorted(path.glob("*.jsonl"))
    raise FileNotFoundError(f"Input path does not exist: {input_path}")


def _refresh_run_summaries(
    summary_dir: Path,
    evaluated_dir: Path,
    raw_dir: Path,
    aggregate_outputs: Dict[str, str],
    config: Dict[str, Any],
) -> None:
    """Refresh existing run summary JSON files after evaluated files are overwritten."""
    grouped_records: dict[tuple[str, str, str], list[Dict[str, Any]]] = defaultdict(list)
    grouped_dataset_records: dict[tuple[str, str, str], dict[str, list[Dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    grouped_dataset_files: dict[tuple[str, str, str], dict[str, str]] = defaultdict(dict)

    for evaluated_file in sorted(evaluated_dir.glob("*.jsonl")):
        records = read_jsonl(str(evaluated_file))
        if not records:
            continue
        key = (
            str(records[0].get("run_id", "")),
            str(records[0].get("model_alias", "")),
            str(records[0].get("method_name", "")),
        )
        dataset_name = str(records[0].get("dataset_name", ""))
        grouped_records[key].extend(records)
        grouped_dataset_records[key][dataset_name].extend(records)
        grouped_dataset_files[key][dataset_name] = str(evaluated_file)

    summary_payloads: dict[tuple[str, str, str], dict[str, Any]] = {}
    for summary_path in sorted(summary_dir.glob("run_summary__*.json")):
        summary = json.loads(summary_path.read_text(encoding = "utf-8"))
        key = (
            str(summary.get("run_id", "")),
            str(summary.get("model_alias", "")),
            str(summary.get("method_name", "")),
        )
        summary_payloads[key] = {"payload": summary, "path": summary_path}

    for key, records in grouped_records.items():
        run_id, model_alias, method_name = key
        summary_info = summary_payloads.get(key, {})
        summary = summary_info.get("payload", {})
        if not records:
            continue

        first_record = records[0]
        model_name = str(first_record.get("model_name", model_alias))

        dataset_summaries: List[Dict[str, Any]] = []
        existing_dataset_entries = {
            str(entry.get("dataset_name", "")): entry
            for entry in summary.get("datasets", [])
            if isinstance(entry, dict)
        }

        existing_dataset_order = [
            str(entry.get("dataset_name", ""))
            for entry in summary.get("datasets", [])
            if isinstance(entry, dict)
        ]
        dataset_order = [name for name in existing_dataset_order if name in grouped_dataset_records[key]]
        dataset_order.extend(
            name for name in grouped_dataset_records[key].keys()
            if name not in existing_dataset_entries
        )

        for dataset_name in dataset_order:
            records = grouped_dataset_records[key][dataset_name]
            dataset_summary = summarize_records(records)
            existing_entry = existing_dataset_entries.get(dataset_name, {})
            dataset_summary["raw_file"] = existing_entry.get(
                "raw_file",
                str(raw_dir / Path(grouped_dataset_files[key][dataset_name]).name),
            )
            dataset_summary["evaluated_file"] = grouped_dataset_files[key].get(dataset_name, existing_entry.get("evaluated_file", ""))
            dataset_summaries.append(dataset_summary)

        overall_summary = summarize_records(grouped_records[key])
        overall_summary["dataset_name"] = "overall"
        overall_summary["aggregate_scores_path"] = aggregate_outputs["aggregate_scores"]
        overall_summary["single_metric_stats_path"] = aggregate_outputs["single_metric_stats"]

        if not summary:
            summary = {
                "run_id": run_id,
                "model_name": model_name,
                "model_alias": model_alias,
                "method_name": method_name,
                "model_settings": get_model_settings(config, model_name),
                "artifacts": {
                    "raw_dir": str(raw_dir),
                    "evaluated_dir": str(evaluated_dir),
                    "summary_dir": str(summary_dir),
                    "log_dir": str(Path(config["run"]["log_dir"])),
                    **aggregate_outputs,
                },
            }
            summary_path = summary_dir / f"run_summary__{run_id}__{model_alias}__{method_name}.json"
        else:
            summary_path = summary_info["path"]

        summary["run_id"] = run_id
        summary["model_name"] = model_name
        summary["model_alias"] = model_alias
        summary["method_name"] = method_name
        summary["model_settings"] = summary.get("model_settings") or get_model_settings(config, model_name)
        summary["datasets"] = dataset_summaries
        summary["overall"] = overall_summary
        if not isinstance(summary.get("artifacts"), dict):
            summary["artifacts"] = {}
        summary["artifacts"].update(
            {
                "raw_dir": str(raw_dir),
                "evaluated_dir": str(evaluated_dir),
                "summary_dir": str(summary_dir),
                "log_dir": str(Path(config["run"]["log_dir"])),
                **aggregate_outputs,
            }
        )

        summary_path.write_text(json.dumps(summary, ensure_ascii = False, indent = 2), encoding = "utf-8")


def overwrite_inputs(
    input_path: str,
    config_path: str,
) -> List[Dict[str, Any]]:
    """Overwrite one file or one directory of evaluated files after recalculation."""
    config = load_experiment_config(config_path)
    scoring_config = config.get("scoring", {})
    results: List[Dict[str, Any]] = []

    for file_path in _iter_input_files(input_path):
        existing_records = read_jsonl(str(file_path))
        if not existing_records:
            results.append(
                {
                    "file": str(file_path),
                    "sample_count": 0,
                    "skipped": True,
                    "reason": "empty_input_file",
                }
            )
            continue
        updated_records, rows = recalculate_file(str(file_path), scoring_config = scoring_config)
        write_jsonl(str(file_path), updated_records)
        results.append(
            {
                "file": str(file_path),
                "sample_count": len(updated_records),
                **_build_summary(rows),
            }
        )

    aggregate_outputs = summarize_all(config_path)
    _refresh_run_summaries(
        summary_dir = Path(config["run"]["summary_dir"]),
        evaluated_dir = Path(config["run"]["evaluated_dir"]),
        raw_dir = Path(config["run"]["output_dir"]),
        aggregate_outputs = aggregate_outputs,
        config = config,
    )
    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description = "Recalculate sample-level score_i from evaluated JSONL and print or overwrite results.")
    parser.add_argument("--input", required = True, help = "Path to one evaluated JSONL file or a directory of evaluated JSONL files.")
    parser.add_argument("--config", default = None, help = "Optional YAML config path. Required for overwrite mode and used to load scoring settings.")
    parser.add_argument("--sample-id", action = "append", default = None, help = "Optional sample_id filter. Can be passed multiple times. Only valid for preview mode.")
    parser.add_argument("--limit", type = int, default = None, help = "Optional maximum number of printed samples. Only valid for preview mode.")
    parser.add_argument("--mean-only", action = "store_true", help = "Only print the recalculated aggregate mean summary for the selected records.")
    parser.add_argument("--overwrite", action = "store_true", help = "Overwrite the target evaluated file(s) in place and refresh summary files.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.overwrite:
        if not args.config:
            raise ValueError("--overwrite 模式必须提供 --config。")
        results = overwrite_inputs(args.input, config_path = args.config)
        for item in results:
            print(json.dumps(item, ensure_ascii = False))
        return

    updated_records, rows = recalculate_file(
        evaluated_path = args.input,
        scoring_config = _resolve_scoring_config(args.config),
    )
    if args.sample_id:
        selected_sample_ids = set(args.sample_id)
        rows = [row for row in rows if str(row.get("sample_id", "")) in selected_sample_ids]
    if args.limit is not None and args.limit >= 0:
        rows = rows[:args.limit]

    _print_results(rows, evaluated_path = args.input, mean_only = args.mean_only)


if __name__ == "__main__":
    main()
