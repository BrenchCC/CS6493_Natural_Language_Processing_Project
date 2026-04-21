"""
Evaluate raw inference outputs and compute per-sample score features.
"""

import os
import sys
import copy
import argparse
import logging
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List

# Add project root to Python path
sys.path.append(os.getcwd())

from evaluation.io_utils import read_jsonl
from evaluation.io_utils import write_jsonl
from evaluation.metrics import collect_metrics
from evaluation.scoring import compute_score
from infer_exp.config_utils import ensure_dir
from infer_exp.config_utils import load_yaml_config


logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Args:
        None.
    """
    parser = argparse.ArgumentParser(description = "Evaluate raw run outputs.")
    parser.add_argument(
        "--config",
        type = str,
        required = True,
        help = "Path to YAML config file."
    )
    return parser.parse_args()


def _resolve_length_override(
    scoring_config: Dict[str, Any],
    record: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Apply dataset/method length override for scoring params.

    Args:
        scoring_config: Base scoring config dictionary.
        record: Inference record.
    """
    resolved = copy.deepcopy(scoring_config)
    overrides = resolved.pop("length_overrides", [])
    if not isinstance(overrides, list):
        return resolved

    dataset_name = record.get("dataset", "")
    method_name = record.get("method", "")

    for item in overrides:
        if not isinstance(item, dict):
            continue
        if item.get("dataset") not in [None, "", dataset_name]:
            continue
        if item.get("method") not in [None, "", method_name]:
            continue

        params = resolved.setdefault("params", {})
        if "L_ref" in item:
            params["L_ref"] = item["L_ref"]
        if "tau_d" in item:
            params["tau_d"] = item["tau_d"]
    return resolved


def _collect_raw_result_files(raw_dir: str) -> List[Path]:
    """
    Collect raw JSONL result files from directory.

    Args:
        raw_dir: Raw output directory path.
    """
    root = Path(raw_dir)
    if not root.exists():
        return []
    return sorted(root.glob("*.jsonl"))


def evaluate_runs(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Evaluate all raw run files according to config.

    Args:
        config: Experiment configuration dictionary.
    """
    run_cfg = config.get("run", {})
    scoring_cfg = copy.deepcopy(config.get("scoring", {}))

    raw_dir = run_cfg.get("output_dir", "results/raw")
    evaluated_dir = run_cfg.get("evaluated_dir", "results/evaluated")
    ensure_dir(evaluated_dir)

    evaluated_manifest = []
    raw_files = _collect_raw_result_files(raw_dir)
    if not raw_files:
        logger.warning("No raw files found in %s", raw_dir)
        return evaluated_manifest

    for raw_file in raw_files:
        records = read_jsonl(str(raw_file))
        if not records:
            continue

        output_records = []
        for item in records:
            raw_output = str(item.get("raw_output", ""))
            ground_truth = str(item.get("ground_truth", ""))
            final_answer = item.get("final_answer")

            metrics = collect_metrics(
                raw_output = raw_output,
                ground_truth = ground_truth,
                final_answer = final_answer
            )
            resolved_scoring = _resolve_length_override(scoring_cfg, item)
            factors = compute_score(metrics = metrics, scoring_config = resolved_scoring)

            output = dict(item)
            output.update(metrics)
            output.update(factors)
            output_records.append(output)

        evaluated_path = Path(evaluated_dir) / raw_file.name
        write_jsonl(str(evaluated_path), output_records)

        manifest_item = {
            "raw_file": str(raw_file),
            "evaluated_file": str(evaluated_path),
            "num_records": len(output_records)
        }
        evaluated_manifest.append(manifest_item)
        logger.info(
            "Evaluated %d records from %s",
            len(output_records),
            raw_file.name
        )

    return evaluated_manifest


def main() -> None:
    """
    Run CLI entrypoint.

    Args:
        None.
    """
    args = parse_args()
    config = load_yaml_config(args.config)
    manifest = evaluate_runs(config)

    run_cfg = config.get("run", {})
    evaluated_dir = run_cfg.get("evaluated_dir", "results/evaluated")
    manifest_path = Path(evaluated_dir) / "evaluation_manifest.json"

    import json

    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii = False, indent = 2),
        encoding = "utf-8"
    )
    logger.info("Evaluation manifest saved to %s", str(manifest_path))


if __name__ == "__main__":
    logging.basicConfig(
        level = logging.INFO,
        format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers = [logging.StreamHandler()]
    )
    main()
