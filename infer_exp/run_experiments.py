"""
Run math reasoning experiments with local vLLM loading and threaded scheduling.
"""

import os
import sys
import copy
import time
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
from typing import Any
from typing import Dict
from typing import List

# Add project root to Python path
sys.path.append(os.getcwd())

from evaluation.io_utils import read_jsonl
from evaluation.io_utils import write_jsonl
from evaluation.metrics import extract_final_answer
from infer_exp.config_utils import ensure_dir
from infer_exp.config_utils import load_yaml_config
from infer_exp.execution_utils import execute_python_code
from infer_exp.execution_utils import extract_last_python_block
from prompts import get_prompt_method
from vllm_server.local_engine import LocalVLLMEngine


logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Args:
        None.
    """
    parser = argparse.ArgumentParser(description = "Run local vLLM experiments.")
    parser.add_argument(
        "--config",
        type = str,
        required = True,
        help = "Path to YAML config file."
    )
    return parser.parse_args()


def _sanitize_model_name(model_id: str) -> str:
    """
    Convert model id into file-safe model alias.

    Args:
        model_id: Hugging Face model id.
    """
    return model_id.replace("/", "__")


def _chunk_list(items: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split list into chunks.

    Args:
        items: Input list.
        chunk_size: Target chunk size.
    """
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


def _normalize_method_entries(method_entries: List[Any]) -> List[Dict[str, Any]]:
    """
    Normalize method config entries.

    Args:
        method_entries: Raw method list from config.
    """
    normalized = []
    for item in method_entries:
        if isinstance(item, str):
            normalized.append({"name": item, "enabled": True})
        elif isinstance(item, dict):
            entry = dict(item)
            entry.setdefault("enabled", True)
            normalized.append(entry)
        else:
            raise ValueError(f"Unsupported method entry type: {type(item)}")
    return [item for item in normalized if item.get("enabled", True)]


def _resolve_dataset_samples(dataset_cfg: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Load dataset samples from configured JSONL file.

    Args:
        dataset_cfg: Dataset configuration dictionary.
    """
    sample_path = dataset_cfg.get("sample_path")
    if not sample_path:
        raise ValueError(f"Missing sample_path for dataset: {dataset_cfg}")

    samples = read_jsonl(sample_path)
    max_samples = int(dataset_cfg.get("max_samples", -1))
    if max_samples > 0:
        samples = samples[:max_samples]
    return samples


def _prepare_prompt_item(
    method_name: str,
    method_config: Dict[str, Any],
    sample: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Build prompt payload for one sample.

    Args:
        method_name: Prompt method name.
        method_config: Method-level config dictionary.
        sample: Dataset sample record.
    """
    method = get_prompt_method(method_name, method_config)
    problem = str(sample.get("question", ""))
    prompt = method.build_prompt(problem = problem)

    return {
        "sample": sample,
        "problem": problem,
        "prompt": prompt,
        "decode": method.decode_strategy(),
        "method": method
    }


def _base_record(
    model_id: str,
    dataset_name: str,
    method_name: str,
    sample: Dict[str, Any],
    raw_output: str,
    final_answer: str,
    extra: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Build standardized inference output record.

    Args:
        model_id: Model identifier.
        dataset_name: Dataset name.
        method_name: Prompt method name.
        sample: Original sample record.
        raw_output: Full output text.
        final_answer: Extracted final answer.
        extra: Optional extra fields.
    """
    record = {
        "sample_id": sample.get("id", sample.get("sample_id", sample.get("idx", ""))),
        "dataset": dataset_name,
        "method": method_name,
        "model_id": model_id,
        "question": sample.get("question", ""),
        "ground_truth": sample.get("answer", sample.get("ground_truth", "")),
        "raw_output": raw_output,
        "final_answer": final_answer,
        "response_length_tokens": len(raw_output.split()),
        "response_length_chars": len(raw_output)
    }
    if extra:
        record.update(extra)
    return record


def _run_single_pass_method(
    model_id: str,
    dataset_name: str,
    method_name: str,
    method_config: Dict[str, Any],
    samples: List[Dict[str, Any]],
    engine: LocalVLLMEngine,
    num_workers: int,
    micro_batch_size: int
) -> List[Dict[str, Any]]:
    """
    Run one-pass methods with threaded prompt building and micro-batch generation.

    Args:
        model_id: Model identifier.
        dataset_name: Dataset name.
        method_name: Prompt method name.
        method_config: Method-level config.
        samples: Dataset samples.
        engine: Local vLLM engine.
        num_workers: Thread worker count.
        micro_batch_size: Batch size for generation.
    """
    prompt_items = []
    with ThreadPoolExecutor(max_workers = num_workers) as executor:
        futures = [
            executor.submit(
                _prepare_prompt_item,
                method_name,
                method_config,
                sample
            )
            for sample in samples
        ]
        for future in as_completed(futures):
            prompt_items.append(future.result())

    prompt_items.sort(key = lambda item: str(item["sample"].get("id", item["sample"].get("idx", ""))))
    outputs = []
    for chunk in _chunk_list(prompt_items, max(1, micro_batch_size)):
        prompts = [item["prompt"] for item in chunk]
        decode = chunk[0]["decode"] if chunk else {}
        chunk_outputs = engine.generate_batch(prompts = prompts, decode_config = decode)
        outputs.extend(list(zip(chunk, chunk_outputs)))

    records = []
    for item, raw_text in outputs:
        answer = extract_final_answer(raw_text)
        record = _base_record(
            model_id = model_id,
            dataset_name = dataset_name,
            method_name = method_name,
            sample = item["sample"],
            raw_output = raw_text,
            final_answer = answer,
            extra = {
                "prompt": item["prompt"],
                "decode_config": item["decode"]
            }
        )
        records.append(record)
    return records


def _self_consistency_worker(
    sample: Dict[str, Any],
    model_id: str,
    dataset_name: str,
    method_name: str,
    method_config: Dict[str, Any],
    engine: LocalVLLMEngine
) -> Dict[str, Any]:
    """
    Run self-consistency inference for one sample.

    Args:
        sample: Dataset sample record.
        model_id: Model identifier.
        dataset_name: Dataset name.
        method_name: Prompt method name.
        method_config: Method-level config.
        engine: Local vLLM engine.
    """
    method = get_prompt_method(method_name, method_config)
    problem = str(sample.get("question", ""))
    prompt = method.build_prompt(problem = problem)
    decode = method.decode_strategy()

    n_samples = int(method_config.get("n_samples", 5))
    prompts = [prompt] * max(1, n_samples)
    candidates = engine.generate_batch(prompts = prompts, decode_config = decode)
    candidate_answers = [extract_final_answer(text) for text in candidates]
    aggregate = method.aggregate(candidates, candidate_answers)

    raw_output = "\n\n".join(candidates)
    return _base_record(
        model_id = model_id,
        dataset_name = dataset_name,
        method_name = method_name,
        sample = sample,
        raw_output = raw_output,
        final_answer = aggregate.get("final_answer", ""),
        extra = {
            "prompt": prompt,
            "decode_config": decode,
            "raw_candidates": candidates,
            "candidate_answers": candidate_answers,
            "vote_count": aggregate.get("vote_count", 0),
            "vote_ratio": aggregate.get("vote_ratio", 0.0),
            "vote_entropy": aggregate.get("vote_entropy", 0.0)
        }
    )


def _self_refine_worker(
    sample: Dict[str, Any],
    model_id: str,
    dataset_name: str,
    method_name: str,
    method_config: Dict[str, Any],
    engine: LocalVLLMEngine
) -> Dict[str, Any]:
    """
    Run self-refine inference for one sample.

    Args:
        sample: Dataset sample record.
        model_id: Model identifier.
        dataset_name: Dataset name.
        method_name: Prompt method name.
        method_config: Method-level config.
        engine: Local vLLM engine.
    """
    method = get_prompt_method(method_name, method_config)
    problem = str(sample.get("question", ""))
    decode = method.decode_strategy()

    initial_prompt = method.build_prompt(problem = problem)
    draft_output = engine.generate_text(prompt = initial_prompt, decode_config = decode)

    refine_prompt = method.build_refine_prompt(problem = problem, draft = draft_output)
    refined_output = engine.generate_text(prompt = refine_prompt, decode_config = decode)
    final_answer = extract_final_answer(refined_output)

    raw_output = (
        f"[draft]\n{draft_output}\n\n"
        f"[refined]\n{refined_output}"
    )
    return _base_record(
        model_id = model_id,
        dataset_name = dataset_name,
        method_name = method_name,
        sample = sample,
        raw_output = raw_output,
        final_answer = final_answer,
        extra = {
            "prompt_initial": initial_prompt,
            "prompt_refine": refine_prompt,
            "decode_config": decode
        }
    )


def _tir_worker(
    sample: Dict[str, Any],
    model_id: str,
    dataset_name: str,
    method_name: str,
    method_config: Dict[str, Any],
    engine: LocalVLLMEngine
) -> Dict[str, Any]:
    """
    Run tool-integrated reasoning for one sample.

    Args:
        sample: Dataset sample record.
        model_id: Model identifier.
        dataset_name: Dataset name.
        method_name: Prompt method name.
        method_config: Method-level config.
        engine: Local vLLM engine.
    """
    method = get_prompt_method(method_name, method_config)
    problem = str(sample.get("question", ""))
    decode = method.decode_strategy()
    timeout_sec = int(method_config.get("exec_timeout_sec", 8))
    python_mode = str(method_config.get("exec_python_mode", "current"))
    conda_env = str(method_config.get("exec_conda_env", ""))

    initial_prompt = method.build_prompt(problem = problem)
    draft_output = engine.generate_text(prompt = initial_prompt, decode_config = decode)

    code = extract_last_python_block(draft_output)
    if code:
        exec_feedback = execute_python_code(
            code = code,
            timeout_sec = timeout_sec,
            python_mode = python_mode,
            conda_env = conda_env
        )
        feedback_text = (
            "```output\n"
            f"status = {exec_feedback['status']}\n"
            f"stdout = {exec_feedback['stdout']}\n"
            f"stderr = {exec_feedback['stderr']}\n"
            "```"
        )
    else:
        exec_feedback = {
            "status": "no_code",
            "stdout": "",
            "stderr": "No Python block detected.",
            "return_code": "-1"
        }
        feedback_text = "```output\nNo Python block detected.\n```"

    follow_prompt = method.build_feedback_prompt(
        problem = problem,
        draft = draft_output,
        feedback = feedback_text
    )
    final_output = engine.generate_text(prompt = follow_prompt, decode_config = decode)
    final_answer = extract_final_answer(final_output)

    raw_output = (
        f"[draft]\n{draft_output}\n\n"
        f"[feedback]\n{feedback_text}\n\n"
        f"[final]\n{final_output}"
    )
    return _base_record(
        model_id = model_id,
        dataset_name = dataset_name,
        method_name = method_name,
        sample = sample,
        raw_output = raw_output,
        final_answer = final_answer,
        extra = {
            "prompt_initial": initial_prompt,
            "prompt_follow": follow_prompt,
            "decode_config": decode,
            "executed_code": code or "",
            "execution_feedback": exec_feedback,
            "exec_python_mode": python_mode,
            "exec_conda_env": conda_env
        }
    )


def _sr_sd_tir_worker(
    sample: Dict[str, Any],
    model_id: str,
    dataset_name: str,
    method_name: str,
    method_config: Dict[str, Any],
    engine: LocalVLLMEngine
) -> Dict[str, Any]:
    """
    Run SR-SD-TIR staged inference for one sample.

    Args:
        sample: Dataset sample record.
        model_id: Model identifier.
        dataset_name: Dataset name.
        method_name: Prompt method name.
        method_config: Method-level config.
        engine: Local vLLM engine.
    """
    method = get_prompt_method(method_name, method_config)
    problem = str(sample.get("question", ""))
    decode = method.decode_strategy()
    timeout_sec = int(method_config.get("exec_timeout_sec", 8))
    python_mode = str(method_config.get("exec_python_mode", "current"))
    conda_env = str(method_config.get("exec_conda_env", ""))

    plan_prompt = method.build_prompt(problem = problem)
    plan_output = engine.generate_text(prompt = plan_prompt, decode_config = decode)

    solve_prompt = method.build_solve_prompt(problem = problem, plan = plan_output)
    solve_output = engine.generate_text(prompt = solve_prompt, decode_config = decode)

    code = extract_last_python_block(solve_output)
    if code:
        exec_feedback = execute_python_code(
            code = code,
            timeout_sec = timeout_sec,
            python_mode = python_mode,
            conda_env = conda_env
        )
        feedback_text = (
            "Execution feedback:\n"
            f"status = {exec_feedback['status']}\n"
            f"stdout = {exec_feedback['stdout']}\n"
            f"stderr = {exec_feedback['stderr']}"
        )
    else:
        exec_feedback = {
            "status": "no_code",
            "stdout": "",
            "stderr": "No Python block detected.",
            "return_code": "-1"
        }
        feedback_text = "Execution feedback:\nNo Python block detected."

    reflect_input = f"{solve_output}\n\n{feedback_text}"
    reflect_prompt = method.build_reflect_prompt(problem = problem, solution = reflect_input)
    reflect_output = engine.generate_text(prompt = reflect_prompt, decode_config = decode)
    final_answer = extract_final_answer(reflect_output)

    raw_output = (
        f"[plan]\n{plan_output}\n\n"
        f"[solve]\n{solve_output}\n\n"
        f"[feedback]\n{feedback_text}\n\n"
        f"[reflect]\n{reflect_output}"
    )
    return _base_record(
        model_id = model_id,
        dataset_name = dataset_name,
        method_name = method_name,
        sample = sample,
        raw_output = raw_output,
        final_answer = final_answer,
        extra = {
            "prompt_plan": plan_prompt,
            "prompt_solve": solve_prompt,
            "prompt_reflect": reflect_prompt,
            "decode_config": decode,
            "executed_code": code or "",
            "execution_feedback": exec_feedback,
            "exec_python_mode": python_mode,
            "exec_conda_env": conda_env
        }
    )


def _run_threaded_method(
    worker_fn,
    samples: List[Dict[str, Any]],
    num_workers: int,
    *worker_args
) -> List[Dict[str, Any]]:
    """
    Run per-sample worker in thread pool.

    Args:
        worker_fn: Callable worker function.
        samples: Dataset sample list.
        num_workers: Thread worker count.
        *worker_args: Extra positional arguments for worker function.
    """
    records = []
    with ThreadPoolExecutor(max_workers = num_workers) as executor:
        futures = [executor.submit(worker_fn, sample, *worker_args) for sample in samples]
        for future in as_completed(futures):
            records.append(future.result())

    records.sort(key = lambda item: str(item.get("sample_id", "")))
    return records


def _run_method(
    model_id: str,
    dataset_name: str,
    method_name: str,
    method_config: Dict[str, Any],
    samples: List[Dict[str, Any]],
    engine: LocalVLLMEngine,
    run_cfg: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Dispatch runtime path by method type.

    Args:
        model_id: Model identifier.
        dataset_name: Dataset name.
        method_name: Prompt method name.
        method_config: Method-level config.
        samples: Dataset sample records.
        engine: Local vLLM engine.
        run_cfg: Runtime config dictionary.
    """
    num_workers = int(run_cfg.get("num_workers", 4))
    micro_batch_size = int(run_cfg.get("micro_batch_size", 8))

    if method_name in ["cot_zero", "cot_few_shot"]:
        return _run_single_pass_method(
            model_id = model_id,
            dataset_name = dataset_name,
            method_name = method_name,
            method_config = method_config,
            samples = samples,
            engine = engine,
            num_workers = num_workers,
            micro_batch_size = micro_batch_size
        )

    if method_name == "self_consistency":
        return _run_threaded_method(
            _self_consistency_worker,
            samples,
            num_workers,
            model_id,
            dataset_name,
            method_name,
            method_config,
            engine
        )

    if method_name == "self_refine":
        return _run_threaded_method(
            _self_refine_worker,
            samples,
            num_workers,
            model_id,
            dataset_name,
            method_name,
            method_config,
            engine
        )

    if method_name == "tir":
        return _run_threaded_method(
            _tir_worker,
            samples,
            num_workers,
            model_id,
            dataset_name,
            method_name,
            method_config,
            engine
        )

    if method_name == "sr_sd_tir":
        return _run_threaded_method(
            _sr_sd_tir_worker,
            samples,
            num_workers,
            model_id,
            dataset_name,
            method_name,
            method_config,
            engine
        )

    raise ValueError(f"Unsupported method for runtime dispatch: {method_name}")


def run_experiments(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute experiment matrix from config.

    Args:
        config: Experiment configuration dictionary.
    """
    run_cfg = copy.deepcopy(config.get("run", {}))
    output_dir = run_cfg.get("output_dir", "results/raw")
    ensure_dir(output_dir)

    timestamp_tag = datetime.now().strftime("%Y%m%d_%H%M%S")
    models = config.get("models", [])
    datasets = config.get("datasets", [])
    methods = _normalize_method_entries(config.get("methods", []))
    method_cfg_map = config.get("method_configs", {})
    vllm_cfg = config.get("vllm", {})

    summary = {
        "timestamp": timestamp_tag,
        "runs": []
    }

    for model_entry in models:
        model_id = model_entry["id"] if isinstance(model_entry, dict) else str(model_entry)
        logger.info("Loading model: %s", model_id)
        engine = LocalVLLMEngine(model_id = model_id, engine_config = vllm_cfg)

        for dataset_cfg in datasets:
            dataset_name = dataset_cfg["name"]
            samples = _resolve_dataset_samples(dataset_cfg)
            logger.info("Dataset %s loaded with %d samples.", dataset_name, len(samples))

            for method_entry in methods:
                method_name = method_entry["name"]
                method_config = copy.deepcopy(method_cfg_map.get(method_name, {}))
                logger.info(
                    "Running model=%s dataset=%s method=%s",
                    model_id,
                    dataset_name,
                    method_name
                )
                started = time.time()
                records = _run_method(
                    model_id = model_id,
                    dataset_name = dataset_name,
                    method_name = method_name,
                    method_config = method_config,
                    samples = samples,
                    engine = engine,
                    run_cfg = run_cfg
                )
                elapsed = time.time() - started

                model_alias = _sanitize_model_name(model_id)
                output_file = (
                    f"{output_dir}/{model_alias}__{dataset_name}__{method_name}__{timestamp_tag}.jsonl"
                )
                write_jsonl(output_file, records)
                logger.info("Saved %d records to %s", len(records), output_file)

                summary["runs"].append(
                    {
                        "model_id": model_id,
                        "dataset": dataset_name,
                        "method": method_name,
                        "output_file": output_file,
                        "num_samples": len(records),
                        "elapsed_sec": elapsed
                    }
                )

        del engine

    summary_path = f"{output_dir}/run_summary__{timestamp_tag}.json"
    Path(summary_path).write_text(
        json.dumps(summary, ensure_ascii = False, indent = 2),
        encoding = "utf-8"
    )
    logger.info("Experiment summary saved to %s", summary_path)
    return summary


def main() -> None:
    """
    Run CLI entrypoint.

    Args:
        None.
    """
    args = parse_args()
    config = load_yaml_config(args.config)
    run_experiments(config)


if __name__ == "__main__":
    logging.basicConfig(
        level = logging.INFO,
        format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers = [logging.StreamHandler()]
    )
    main()
