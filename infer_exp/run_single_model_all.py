"""Run one model and one or more methods across three datasets."""

from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path
from pprint import pformat
from typing import Any
from typing import Dict
from typing import List

from evaluation.evaluate_runs import evaluate_raw_file
from evaluation.io_utils import read_jsonl
from evaluation.io_utils import write_jsonl
from evaluation.summarize_scores import summarize_records
from infer_exp.config_utils import filter_named_items
from infer_exp.config_utils import get_model_settings
from infer_exp.config_utils import load_experiment_config
from infer_exp.config_utils import model_alias
from infer_exp.config_utils import parse_csv_filter
from infer_exp.config_utils import resolve_model_path
from prompts import get_available_methods
from prompts import get_prompt_method
from tqdm import tqdm
from vllm_server.server import VLLMEngine


def _load_samples(sample_path: str, max_samples: int | None = None) -> List[Dict[str, Any]]:
    records = read_jsonl(sample_path)
    if max_samples is None or max_samples <= 0:
        return records
    return records[:max_samples]


def _build_engine(config: Dict[str, Any], model_name: str) -> VLLMEngine:
    vllm_config = config.get("vllm", {})
    return VLLMEngine(
        model_path = resolve_model_path(config, model_name),
        tensor_parallel_size = int(vllm_config.get("tensor_parallel_size", 1)),
        gpu_memory_utilization = float(vllm_config.get("gpu_memory_utilization", 0.9)),
        max_model_len = vllm_config.get("max_model_len"),
    )


def _build_raw_record(
    sample: Dict[str, Any],
    run_id: str,
    model_name: str,
    method_name: str,
    dataset_name: str,
    method_result: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "run_id": run_id,
        "timestamp": run_id,
        "model_name": model_name,
        "model_alias": model_alias(model_name),
        "method_name": method_name,
        "dataset_name": dataset_name,
        "sample_id": sample.get("id"),
        "question": sample.get("question", ""),
        "gold_answer": sample.get("answer", ""),
        "input_messages": method_result.get("input_messages", []),
        "raw_response": method_result.get("raw_response", ""),
        "final_response": method_result.get("final_response", ""),
        "intermediate_outputs": method_result.get("intermediate_outputs", []),
        "metadata": method_result.get("metadata", {}),
        "error": method_result.get("error"),
    }


def _build_log_event(run_id: str, level: str, event: str, **payload: Any) -> Dict[str, Any]:
    return {
        "run_id": run_id,
        "timestamp": datetime.utcnow().isoformat(timespec = "seconds") + "Z",
        "level": level,
        "event": event,
        **payload,
    }


def _format_console_log(event_record: Dict[str, Any]) -> str:
    parts = [
        f"[{event_record.get('timestamp', '')}]",
        f"[{event_record.get('level', 'INFO')}]",
        f"[{event_record.get('run_id', '')}]",
        str(event_record.get("event", "log")),
    ]
    payload = {
        key: value
        for key, value in event_record.items()
        if key not in {"timestamp", "level", "run_id", "event"} and value not in (None, "", [], {})
    }
    if payload:
        parts.append(pformat(payload, compact = True, sort_dicts = False))
    return " ".join(parts)


class _RunLogger:
    def __init__(self, run_id: str, log_path: Path) -> None:
        self.run_id = run_id
        self.log_path = log_path
        self.log_path.parent.mkdir(parents = True, exist_ok = True)
        self.log_path.write_text("", encoding = "utf-8")
        self.records: List[Dict[str, Any]] = []
        self.console_logger = logging.getLogger(f"topic1.run.{run_id}")
        self.console_logger.handlers.clear()
        self.console_logger.setLevel(logging.INFO)
        self.console_logger.propagate = False

        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        handler.setFormatter(logging.Formatter("%(message)s"))
        self.console_logger.addHandler(handler)

    def log(self, level: str, event: str, **payload: Any) -> Dict[str, Any]:
        event_record = _build_log_event(self.run_id, level, event, **payload)
        self.records.append(event_record)
        formatted_message = _format_console_log(event_record)
        with self.log_path.open("a", encoding = "utf-8") as file:
            file.write(formatted_message + "\n")
        log_level = getattr(logging, level.upper(), logging.INFO)
        self.console_logger.log(log_level, formatted_message)
        return event_record


def run_one_model_one_method_all_datasets(
    config_path: str,
    model_name: str,
    method_name: str,
    max_samples: int | None = None,
    dataset_filter: List[str] | None = None,
) -> Dict[str, Any]:
    """Run one `(model, method)` pair across all selected datasets."""
    config = load_experiment_config(config_path)
    datasets = filter_named_items(config.get("datasets", []), dataset_filter or [])
    method_config = config.get("method_configs", {}).get(method_name, {})
    method = get_prompt_method(method_name, method_config = method_config)
    run_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    model_settings = get_model_settings(config, model_name)

    raw_dir = Path(config["run"]["output_dir"])
    evaluated_dir = Path(config["run"]["evaluated_dir"])
    log_dir = Path(config["run"].get("log_dir", raw_dir.parent / "logs"))
    log_path = log_dir / f"run_log__{run_id}__{model_alias(model_name)}__{method_name}.log"
    scoring_config = config.get("scoring", {})
    summary_entries: List[Dict[str, Any]] = []
    all_evaluated_records: List[Dict[str, Any]] = []
    logger = _RunLogger(run_id = run_id, log_path = log_path)

    logger.log(
        "INFO",
        "run_started",
        model_name = model_name,
        model_alias = model_alias(model_name),
        method_name = method_name,
        reasoning_mode = model_settings.get("reasoning_mode"),
        enable_thinking = model_settings.get("enable_thinking"),
        cannot_disable_thinking = model_settings.get("cannot_disable_thinking"),
        disable_sampling = model_settings.get("disable_sampling"),
        log_path = str(log_path),
    )
    logger.log("INFO", "engine_build_started", model_name = model_name, model_path = resolve_model_path(config, model_name))
    engine = _build_engine(config, model_name)
    logger.log("INFO", "engine_build_completed", model_name = model_name)

    for dataset in datasets:
        dataset_name = dataset["name"]
        dataset_max = max_samples if max_samples is not None else dataset.get("max_samples")
        samples = _load_samples(dataset["sample_path"], max_samples = int(dataset_max) if dataset_max else None)
        logger.log(
            "INFO",
            "dataset_started",
            dataset_name = dataset_name,
            sample_count = len(samples),
            sample_path = dataset["sample_path"],
        )
        raw_records = []
        progress_bar = tqdm(
            samples,
            total = len(samples),
            desc = f"Infer {dataset_name}/{method_name}",
            dynamic_ncols = True,
        )
        for index, sample in enumerate(progress_bar, start = 1):
            try:
                result = method.run(
                    engine,
                    sample,
                    dataset_name = dataset_name,
                    enable_thinking = model_settings.get("enable_thinking"),
                    model_settings = model_settings,
                )
                raw_records.append(
                    _build_raw_record(
                        sample = sample,
                        run_id = run_id,
                        model_name = model_name,
                        method_name = method_name,
                        dataset_name = dataset_name,
                        method_result = result,
                    )
                )
            except Exception as exc:
                raw_records.append(
                    {
                        "run_id": run_id,
                        "timestamp": run_id,
                        "model_name": model_name,
                        "model_alias": model_alias(model_name),
                        "method_name": method_name,
                        "dataset_name": dataset_name,
                        "sample_id": sample.get("id"),
                        "question": sample.get("question", ""),
                        "gold_answer": sample.get("answer", ""),
                        "input_messages": [],
                        "raw_response": "",
                        "final_response": "",
                        "intermediate_outputs": [],
                        "metadata": {},
                        "error": str(exc),
                    }
                )
                logger.log(
                    "ERROR",
                    "sample_failed",
                    dataset_name = dataset_name,
                    sample_id = sample.get("id"),
                    sample_index = index,
                    sample_count = len(samples),
                    error = str(exc),
                )
        progress_bar.close()

        file_name = f"{model_alias(model_name)}__{dataset_name}__{method_name}__{run_id}.jsonl"
        raw_path = raw_dir / file_name
        evaluated_path = evaluated_dir / file_name
        logger.log("INFO", "raw_write_started", dataset_name = dataset_name, raw_file = str(raw_path))
        write_jsonl(str(raw_path), raw_records)
        logger.log("INFO", "raw_write_completed", dataset_name = dataset_name, raw_file = str(raw_path))
        logger.log(
            "INFO",
            "evaluation_started",
            dataset_name = dataset_name,
            raw_file = str(raw_path),
            evaluated_file = str(evaluated_path),
            eval_num_workers = int(config["run"].get("eval_num_workers", config["run"].get("num_workers", 1))),
        )
        evaluated_records = evaluate_raw_file(
            raw_path,
            evaluated_path,
            scoring_config = scoring_config,
            num_workers = int(config["run"].get("eval_num_workers", config["run"].get("num_workers", 1))),
        )
        all_evaluated_records.extend(evaluated_records)
        dataset_summary = summarize_records(evaluated_records)
        dataset_summary["raw_file"] = str(raw_path)
        dataset_summary["evaluated_file"] = str(evaluated_path)
        summary_entries.append(dataset_summary)
        logger.log(
            "INFO",
            "dataset_completed",
            dataset_name = dataset_name,
            raw_file = str(raw_path),
            evaluated_file = str(evaluated_path),
            sample_count = len(evaluated_records),
            accuracy = dataset_summary.get("accuracy", 0.0),
        )

    from evaluation.summarize_scores import summarize_all

    logger.log("INFO", "summary_started", summary_dir = config["run"]["summary_dir"])
    aggregate_outputs = summarize_all(config_path)
    overall_summary = summarize_records(all_evaluated_records)
    overall_summary["dataset_name"] = "overall"
    overall_summary["aggregate_scores_path"] = aggregate_outputs["aggregate_scores"]
    overall_summary["single_metric_stats_path"] = aggregate_outputs["single_metric_stats"]

    run_summary = {
        "run_id": run_id,
        "model_name": model_name,
        "model_alias": model_alias(model_name),
        "method_name": method_name,
        "model_settings": model_settings,
        "datasets": summary_entries,
        "overall": overall_summary,
        "artifacts": {
            "raw_dir": str(raw_dir),
            "evaluated_dir": str(evaluated_dir),
            "summary_dir": config["run"]["summary_dir"],
            "log_dir": str(log_dir),
            **aggregate_outputs,
        },
    }
    summary_path = Path(config["run"]["summary_dir"]) / f"run_summary__{run_id}__{model_alias(model_name)}__{method_name}.json"
    summary_path.parent.mkdir(parents = True, exist_ok = True)
    summary_path.write_text(json.dumps(run_summary, ensure_ascii = False, indent = 2), encoding = "utf-8")
    logger.log(
        "INFO",
        "run_completed",
        summary_path = str(summary_path),
        log_path = str(log_path),
        aggregate_scores_path = aggregate_outputs["aggregate_scores"],
        single_metric_stats_path = aggregate_outputs["single_metric_stats"],
    )
    return run_summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description = "Run one model across selected datasets and methods.")
    parser.add_argument("--config", required = True, help = "Path to YAML config.")
    parser.add_argument("--model", required = True, help = "Model name or local path.")
    parser.add_argument("--methods", default = "", help = "Comma-separated method names. Empty means all registered methods in config.")
    parser.add_argument("--datasets", default = "", help = "Comma-separated dataset names.")
    parser.add_argument("--max-samples", type = int, default = 0, help = "Optional max samples override.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_experiment_config(args.config)
    configured_methods = list(config.get("method_configs", {}).keys()) or get_available_methods()
    requested_methods = parse_csv_filter(args.methods)
    methods = requested_methods or configured_methods
    datasets = parse_csv_filter(args.datasets)
    max_samples = args.max_samples if args.max_samples > 0 else None

    for method_name in methods:
        run_one_model_one_method_all_datasets(
            config_path = args.config,
            model_name = args.model,
            method_name = method_name,
            max_samples = max_samples,
            dataset_filter = datasets,
        )


if __name__ == "__main__":
    main()
