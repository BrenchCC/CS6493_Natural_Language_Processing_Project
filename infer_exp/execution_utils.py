"""
Utilities for extracting and executing generated Python code blocks.
"""

import subprocess
import sys
import textwrap
import re
import shutil
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple


PYTHON_BLOCK_PATTERN = re.compile(r"```python\s*(.*?)```", re.DOTALL | re.IGNORECASE)


def extract_last_python_block(text: str) -> Optional[str]:
    """
    Extract the last Python fenced code block.

    Args:
        text: Model generated text.
    """
    blocks = PYTHON_BLOCK_PATTERN.findall(text)
    if not blocks:
        return None
    return textwrap.dedent(blocks[-1]).strip()


def execute_python_code(
    code: str,
    timeout_sec: int = 8,
    python_mode: str = "current",
    conda_env: str = ""
) -> Dict[str, str]:
    """
    Execute Python code and capture runtime feedback.

    Args:
        code: Python source code string.
        timeout_sec: Max execution seconds.
        python_mode: Python execution mode. One of: current, conda.
        conda_env: Conda environment name when python_mode is conda.
    """
    command, command_error = _build_python_command(
        code = code,
        python_mode = python_mode,
        conda_env = conda_env
    )
    if command_error:
        return {
            "status": "config_error",
            "stdout": "",
            "stderr": command_error,
            "return_code": "-1",
            "python_mode": python_mode,
            "command": ""
        }

    try:
        process = subprocess.run(
            command,
            capture_output = True,
            text = True,
            timeout = timeout_sec,
            check = False
        )
        return {
            "status": "ok" if process.returncode == 0 else "error",
            "stdout": process.stdout.strip(),
            "stderr": process.stderr.strip(),
            "return_code": str(process.returncode),
            "python_mode": python_mode,
            "command": " ".join(command)
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "timeout",
            "stdout": "",
            "stderr": f"Execution timed out after {timeout_sec} seconds.",
            "return_code": "-1",
            "python_mode": python_mode,
            "command": " ".join(command)
        }


def _build_python_command(
    code: str,
    python_mode: str,
    conda_env: str
) -> Tuple[List[str], str]:
    """
    Build the python command for subprocess execution.

    Args:
        code: Python code string.
        python_mode: Execution mode.
        conda_env: Conda environment name.
    """
    mode = (python_mode or "current").strip().lower()
    if mode not in ["current", "conda"]:
        return [], f"Unsupported python_mode: {python_mode}"

    if mode == "current":
        return [sys.executable, "-c", code], ""

    env_name = (conda_env or "").strip()
    if env_name == "":
        return [], "python_mode is conda but exec_conda_env is empty."
    if shutil.which("conda") is None:
        return [], "Conda executable not found in PATH."

    return ["conda", "run", "-n", env_name, "python", "-c", code], ""
