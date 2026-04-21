"""
CoT zero-shot prompting method.
"""

from typing import Any

from .base import PromptMethod


class CoTZeroShot(PromptMethod):
    """
    Chain-of-thought zero-shot prompting.
    """

    TEMPLATE = (
        "Solve the following math problem step by step. "
        "Show concise but complete reasoning, then provide final answer in \\boxed{{}}\\n\\n"
        "Problem:\\n{problem}\\n\\n"
        "Reasoning:"
    )

    @property
    def name(self) -> str:
        """
        Return method name.

        Args:
            None.
        """
        return "cot_zero"

    def build_prompt(self, problem: str, **kwargs: Any) -> str:
        """
        Build zero-shot CoT prompt.

        Args:
            problem: Input math problem.
            **kwargs: Extra prompt context.
        """
        return self.TEMPLATE.format(problem = problem)
