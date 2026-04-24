"""Tool-Integrated Reasoning prompting."""

from __future__ import annotations

import re
import subprocess
import sys
from typing import Any, Dict, List, Tuple

from .base import PromptMethod
from .few_shot_examples import get_tir_reference_examples


_PY_FENCE_PATTERN = re.compile(r"```python\n(.*?)\n```", re.DOTALL)
_OUTPUT_FENCE_PATTERN = re.compile(r"```output\n(.*?)\n```", re.DOTALL)
_FINAL_ANSWER_PATTERN = re.compile(r"Final\s*Answer\s*:\s*\\boxed\{.*?\}", re.DOTALL)


def _extract_python_blocks(text: str) -> List[Tuple[str, int, int]]:
    """Return list of (code, start_idx, end_idx) for ```python fenced blocks."""
    blocks: List[Tuple[str, int, int]] = []
    for match in _PY_FENCE_PATTERN.finditer(text or ""):
        blocks.append((match.group(1).strip("\n"), match.start(), match.end()))
    return blocks


def _has_output_after(text: str, start_idx: int, end_idx: int) -> bool:
    """Heuristic: check if an ```output block appears after this code block before next code block."""
    if not text:
        return False
    next_py = text.find("```python", end_idx)
    search_end = len(text) if next_py < 0 else next_py
    window = text[end_idx:search_end]
    return "```output" in window


def _extract_output_after(text: str, end_idx: int) -> str:
    """Extract the first ```output block after a code fence end (before next code block)."""
    if not text:
        return ""
    next_py = text.find("```python", end_idx)
    search_end = len(text) if next_py < 0 else next_py
    window = text[end_idx:search_end]
    match = _OUTPUT_FENCE_PATTERN.search(window)
    return (match.group(1).strip("\n") if match else "")


class ToolIntegratedReasoning(PromptMethod):
    """Prompt the model to interleave reasoning with Python snippets, executing them when needed."""

    DEFAULT_SYSTEM_PROMPT = (
        "You are a mathematical reasoning assistant that can mix natural-language reasoning with Python snippets. "
        "When you need to compute, write a Python snippet wrapped in ```python fences and STOP. "
        "I will run the code and send you back the execution result wrapped in ```output fences; then continue. "
        "Do not explain the code output in prose. Do not repeat the answer. Do not give any provisional or intermediate answer before the final line. "
        "End with a final line formatted exactly as `Final Answer: \\boxed{...}`."
    )

    USER_TEMPLATE = """Reference Format Examples:
{examples}

Problem:
{problem}

Please solve the problem step by step. Use Python code blocks only when useful, keep the tool-usage format consistent with the references, do not explain code results in prose, do not repeat the final answer, do not give any provisional or intermediate answer, and end with a final line formatted exactly as `Final Answer: \\boxed{{...}}`."""

    @property
    def name(self) -> str:
        return "tir"

    @property
    def run_mode(self) -> str:
        return "tool_loop"

    def _format_reference_examples(self, dataset_name: str | None) -> str:
        examples = get_tir_reference_examples(dataset_name)
        rendered = []
        for index, (question, answer) in enumerate(examples, start = 1):
            rendered.append(f"Reference {index}\nQuestion: {question}\nSolution:\n{answer}")
        return "\n\n".join(rendered)

    def build_system_prompt(self, problem: str, **kwargs) -> str:
        return str(kwargs.get("system_prompt") or self.config.get("system_prompt") or self.DEFAULT_SYSTEM_PROMPT)

    def build_user_prompt(self, problem: str, **kwargs) -> str:
        dataset_name = kwargs.get("dataset_name")
        return self.USER_TEMPLATE.format(
            examples = self._format_reference_examples(dataset_name),
            problem = problem,
        )

    def _execute_python(self, code: str, timeout_seconds: int) -> Dict[str, Any]:
        """Execute one python block (isolated subprocess) and return a structured record."""
        try:
            # Mimic a notebook/REPL: if the last statement is an expression, print its value.
            # This matches common TIR/ToRA-style code blocks where the last line is `V` (no print).
            wrapped = (
                "import ast\n"
                "import traceback\n"
                f"_CODE = {code!r}\n"
                "if 'input(' in _CODE:\n"
                "    raise RuntimeError('input() is not allowed')\n"
                "_env = {}\n"
                "tree = ast.parse(_CODE, mode='exec')\n"
                "if tree.body and isinstance(tree.body[-1], ast.Expr):\n"
                "    last = tree.body.pop()\n"
                "    exec(compile(tree, '<tir>', 'exec'), _env, _env)\n"
                "    val = eval(compile(ast.Expression(last.value), '<tir>', 'eval'), _env, _env)\n"
                "    if val is not None:\n"
                "        print(val)\n"
                "else:\n"
                "    exec(compile(tree, '<tir>', 'exec'), _env, _env)\n"
            )
            completed = subprocess.run(
                [sys.executable, "-c", wrapped],
                capture_output = True,
                text = True,
                timeout = timeout_seconds,
            )
            stdout = (completed.stdout or "").strip()
            stderr = (completed.stderr or "").strip()
            returncode = int(completed.returncode)
            ok = returncode == 0
            # Prefer stdout for normal runs; otherwise surface stderr.
            output_text = stdout if stdout else stderr
            if not output_text and not ok:
                output_text = f"Non-zero return code: {returncode}"
            return {
                "code": code,
                "wrapped": True,
                "stdout": stdout,
                "stderr": stderr,
                "returncode": returncode,
                "ok": ok,
                "output": output_text,
            }
        except subprocess.TimeoutExpired as exc:
            stdout = (exc.stdout or "").strip() if isinstance(exc.stdout, str) else ""
            stderr = (exc.stderr or "").strip() if isinstance(exc.stderr, str) else ""
            return {
                "code": code,
                "wrapped": True,
                "stdout": stdout,
                "stderr": stderr,
                "returncode": None,
                "ok": False,
                "timeout": True,
                "output": f"Timeout after {timeout_seconds}s",
            }

    def run(self, engine: Any, sample: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        problem = str(sample.get("question", ""))
        messages = self.build_messages(problem = problem, sample = sample, **kwargs)
        decode_strategy = self.resolve_decode_strategy(**kwargs)

        max_tool_rounds = int(self.config.get("max_tool_rounds", 8))
        timeout_seconds = int(self.config.get("python_timeout", 8))
        max_total_code_blocks = int(self.config.get("max_total_code_blocks", 32))

        transcript_parts: List[str] = []
        intermediate_outputs: List[Dict[str, Any]] = []
        executed_blocks = 0

        for tool_round in range(max_tool_rounds + 1):
            responses = engine.chat(messages = messages, **decode_strategy)
            assistant_text = responses[0] if responses else ""
            assistant_text = assistant_text or ""

            tool_used_this_round = False
            truncated_suffix = ""

            # Tool loop policy:
            # - Execute at most ONE python block per round.
            # - If the model emits a python block without an output fence, truncate after the block
            #   to keep a valid (python -> output -> continue) trajectory.
            python_blocks = _extract_python_blocks(assistant_text)
            picked_block: Tuple[str, int, int] | None = None
            had_model_output_block = False
            model_output_text = ""

            for code, start_idx, end_idx in python_blocks:
                if not code.strip():
                    continue
                picked_block = (code, start_idx, end_idx)
                had_model_output_block = _has_output_after(assistant_text, start_idx, end_idx)
                if had_model_output_block:
                    model_output_text = _extract_output_after(assistant_text, end_idx)
                break

            if picked_block is not None and not had_model_output_block:
                code, _start_idx, end_idx = picked_block
                if end_idx < len(assistant_text):
                    truncated_suffix = assistant_text[end_idx:].strip("\n")
                    assistant_text = assistant_text[:end_idx].rstrip()

            transcript_parts.append(assistant_text)
            messages.append({"role": "assistant", "content": assistant_text})

            if picked_block is not None and executed_blocks >= max_total_code_blocks:
                intermediate_outputs.append(
                    {
                        "tool_round": tool_round,
                        "block_index": executed_blocks,
                        "code": picked_block[0],
                        "ok": False,
                        "output": "Skipped execution: reached max_total_code_blocks",
                        "had_model_output_block": bool(had_model_output_block),
                        "model_output": model_output_text,
                    }
                )
                break

            if picked_block is not None and executed_blocks < max_total_code_blocks:
                code, _start_idx, _end_idx = picked_block
                exec_record = self._execute_python(code, timeout_seconds = timeout_seconds)
                exec_record.update(
                    {
                        "tool_round": tool_round,
                        "block_index": executed_blocks,
                        "had_model_output_block": bool(had_model_output_block),
                        "model_output": model_output_text,
                        "model_continuation_truncated": bool(truncated_suffix),
                        "model_continuation_text": truncated_suffix,
                    }
                )
                intermediate_outputs.append(exec_record)
                executed_blocks += 1
                tool_used_this_round = True

                output_block = f"```output\n{exec_record['output']}\n```"
                if had_model_output_block:
                    transcript_parts.append("```output\n(executed)\n" + str(exec_record["output"]) + "\n```")
                else:
                    transcript_parts.append(output_block)
                    messages.append({"role": "user", "content": output_block})

            if _FINAL_ANSWER_PATTERN.search(assistant_text) and not tool_used_this_round:
                break
            if not tool_used_this_round and picked_block is None:
                # No tool call requested; treat as single-pass completion.
                break

        full_transcript = "\n".join([part for part in transcript_parts if part is not None and str(part).strip() != ""]).strip()
        final_response = self.post_process(full_transcript, sample = sample, **kwargs)
        return {
            "input_messages": messages,
            "raw_response": full_transcript,
            "final_response": final_response,
            "intermediate_outputs": intermediate_outputs,
            "metadata": {
                "run_mode": self.run_mode,
                "decode_strategy": decode_strategy,
                "max_tool_rounds": max_tool_rounds,
                "python_timeout": timeout_seconds,
                "executed_blocks": executed_blocks,
            },
        }
