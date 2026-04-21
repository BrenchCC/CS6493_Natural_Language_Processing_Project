"""
Prepare sampled JSONL files for MATH-500, GSM8K, and AIME 2024.
"""

import json
import argparse
import random
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List

from datasets import load_dataset


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Args:
        None.
    """
    parser = argparse.ArgumentParser(description = "Prepare sampled datasets.")
    parser.add_argument("--n", type = int, default = 30, help = "Sample count per dataset.")
    parser.add_argument("--seed", type = int, default = 6493, help = "Random seed.")
    parser.add_argument(
        "--output_dir",
        type = str,
        default = "data/processed",
        help = "Output directory for sampled JSONL files."
    )
    return parser.parse_args()


def _to_record(index: int, item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert dataset example to normalized record.

    Args:
        index: Sample index.
        item: Raw dataset item.
    """
    question = item.get("problem", item.get("question", ""))
    answer = item.get("answer", item.get("solution", ""))
    return {
        "id": f"sample-{index}",
        "question": str(question),
        "answer": str(answer)
    }


def _sample_records(
    records: List[Dict[str, Any]],
    sample_n: int,
    seed: int
) -> List[Dict[str, Any]]:
    """
    Randomly sample records with fixed seed.

    Args:
        records: Input record list.
        sample_n: Number of samples.
        seed: Random seed.
    """
    if sample_n <= 0 or sample_n >= len(records):
        return list(records)
    random.seed(seed)
    return random.sample(records, sample_n)


def _write_jsonl(path: Path, records: List[Dict[str, Any]]) -> None:
    """
    Write JSONL records to disk.

    Args:
        path: Output file path.
        records: Record list.
    """
    path.parent.mkdir(parents = True, exist_ok = True)
    with path.open(mode = "w", encoding = "utf-8") as file:
        for item in records:
            file.write(json.dumps(item, ensure_ascii = False) + "\n")


def prepare_samples(n: int, seed: int, output_dir: str) -> None:
    """
    Prepare sampled files for all required datasets.

    Args:
        n: Sample count per dataset.
        seed: Random seed.
        output_dir: Output directory path.
    """
    out_dir = Path(output_dir)

    math_data = load_dataset("HuggingFaceH4/MATH-500", split = "test")
    math_records = [_to_record(index, item) for index, item in enumerate(math_data)]
    _write_jsonl(
        out_dir / "math500_sample.jsonl",
        _sample_records(math_records, n, seed)
    )

    gsm_dataset = load_dataset("openai/gsm8k", "main")
    gsm_split = "test" if "test" in gsm_dataset else "validation"
    gsm_data = gsm_dataset[gsm_split]
    gsm_records = [_to_record(index, item) for index, item in enumerate(gsm_data)]
    _write_jsonl(
        out_dir / "gsm8k_sample.jsonl",
        _sample_records(gsm_records, n, seed)
    )

    aime_data = load_dataset("HuggingFaceH4/aime_2024", split = "train")
    aime_records = [_to_record(index, item) for index, item in enumerate(aime_data)]
    _write_jsonl(
        out_dir / "aime2024_sample.jsonl",
        _sample_records(aime_records, min(n, 30), seed)
    )


def main() -> None:
    """
    Run CLI entrypoint.

    Args:
        None.
    """
    args = parse_args()
    prepare_samples(n = args.n, seed = args.seed, output_dir = args.output_dir)


if __name__ == "__main__":
    main()
