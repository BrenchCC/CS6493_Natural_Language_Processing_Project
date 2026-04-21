"""
CoT few-shot prompting method.
"""

from typing import Any
from typing import Dict
from typing import List

from .base import PromptMethod


class CoTFewShot(PromptMethod):
    """
    Chain-of-thought few-shot prompting.
    """

    TEMPLATE = (
        "You are a careful math solver. Learn from examples, then solve target problem. "
        "Put final answer in \\boxed{{}}.\\n\\n"
        "{examples}\\n"
        "Target Problem:\\n{problem}\\n\\n"
        "Reasoning:"
    )

    @property
    def name(self) -> str:
        """
        Return method name.

        Args:
            None.
        """
        return "cot_few_shot"

    def _render_examples(self, examples: List[Dict[str, str]]) -> str:
        """
        Render few-shot exemplars.

        Args:
            examples: List of example dictionaries.
        """
        blocks = []
        for index, item in enumerate(examples, start = 1):
            question = item.get("question", "")
            answer = item.get("answer", "")
            blocks.append(
                f"Example {index}:\\n"
                f"Question: {question}\\n"
                f"Answer: {answer}\\n"
            )
        return "\\n".join(blocks).strip()

    def build_prompt(self, problem: str, **kwargs: Any) -> str:
        """
        Build few-shot CoT prompt.

        Args:
            problem: Input math problem.
            **kwargs: Extra prompt context.
        """
        examples = kwargs.get("few_shot_examples", self.config.get("few_shot_examples", []))
        example_text = self._render_examples(examples)
        return self.TEMPLATE.format(examples = example_text, problem = problem)
