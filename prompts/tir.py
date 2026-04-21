"""
Tool-integrated reasoning (TIR) prompting method.
"""

from typing import Any
from typing import Dict
from typing import List

from .base import PromptMethod


class ToolIntegratedReasoning(PromptMethod):
    """
    ToRA-style prompt method with interleaved rationale and Python tool use.
    """

    TEMPLATE = (
        "Integrate step-by-step reasoning and Python code to solve the math problem.\\n\\n"
        "Guidelines:\\n"
        "1. Analyze first, then write Python only when symbolic or arithmetic computation is needed.\\n"
        "2. Put executable code inside a fenced block starting with ```python.\\n"
        "3. Assume execution feedback is returned inside ```output ... ```. Use that feedback to continue reasoning.\\n"
        "4. Prefer exact forms (Sympy Rational, pi, sqrt) instead of decimals when possible.\\n"
        "5. End with final answer in \\boxed{{}} and do not include units in the boxed expression.\\n\\n"
        "Question: {problem}\\n\\n"
        "Solution:"
    )

    FEEDBACK_TEMPLATE = (
        "Continue solving with the trajectory below. Use execution feedback to verify or revise the reasoning.\\n"
        "If already solved, directly provide the final answer in \\boxed{{}}.\\n\\n"
        "Question: {problem}\\n\\n"
        "Current trajectory:\\n{draft}\\n\\n"
        "Execution feedback:\\n{feedback}\\n\\n"
        "Continue:"
    )

    @property
    def name(self) -> str:
        """
        Return method name.

        Args:
            None.
        """
        return "tir"

    def build_prompt(self, problem: str, **kwargs: Any) -> str:
        """
        Build TIR initial prompt.

        Args:
            problem: Input math problem.
            **kwargs: Extra prompt context.
        """
        examples = kwargs.get("few_shot_trajectories", self.config.get("few_shot_trajectories", []))
        prefix = self._render_few_shot(examples)
        core = self.TEMPLATE.format(problem = problem)
        if prefix:
            return f"{prefix}\\n\\n---\\n\\n{core}"
        return core

    def _render_few_shot(self, examples: List[Dict[str, str]]) -> str:
        """
        Render optional few-shot tool-use trajectories.

        Args:
            examples: Few-shot trajectory list.
        """
        if not examples:
            return ""

        rendered = []
        for index, item in enumerate(examples, start = 1):
            question = item.get("question", "")
            trajectory = item.get("trajectory", "")
            rendered.append(
                f"Example {index}:\\n"
                f"Question: {question}\\n\\n"
                f"Solution:\\n{trajectory}"
            )
        return "\\n\\n---\\n\\n".join(rendered)

    def build_feedback_prompt(
        self,
        problem: str,
        draft: str,
        feedback: str
    ) -> str:
        """
        Build follow-up prompt with code feedback.

        Args:
            problem: Input math problem.
            draft: First-pass draft with optional code.
            feedback: Code execution result text.
        """
        return self.FEEDBACK_TEMPLATE.format(
            problem = problem,
            draft = draft,
            feedback = feedback
        )

    def decode_strategy(self) -> Dict[str, Any]:
        """
        Return decoding parameters for TIR.

        Args:
            None.
        """
        params = super().decode_strategy()
        params["temperature"] = self.config.get("temperature", 0.0)
        params["top_p"] = self.config.get("top_p", 1.0)
        return params
