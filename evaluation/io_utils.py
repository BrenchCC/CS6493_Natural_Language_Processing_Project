"""
I/O helpers for evaluation pipeline.
"""

import json
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List


def read_jsonl(path: str) -> List[Dict[str, Any]]:
    """
    Read JSONL records from file.

    Args:
        path: JSONL file path.
    """
    records = []
    file_path = Path(path)
    if not file_path.exists():
        return records

    with file_path.open(mode = "r", encoding = "utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def write_jsonl(path: str, records: List[Dict[str, Any]]) -> None:
    """
    Write JSONL records to file.

    Args:
        path: Output JSONL file path.
        records: Record list.
    """
    file_path = Path(path)
    file_path.parent.mkdir(parents = True, exist_ok = True)
    with file_path.open(mode = "w", encoding = "utf-8") as file:
        for item in records:
            file.write(json.dumps(item, ensure_ascii = False) + "\n")
