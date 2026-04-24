"""Few-shot CoT prompting."""

from .base import PromptMethod
from .few_shot_examples import get_few_shot_examples


class CoTFewShot(PromptMethod):
    """Few-shot CoT prompting with dataset-aware exemplars."""

    DEFAULT_SYSTEM_PROMPT = """You are a careful mathematical reasoning assistant. Follow the style of the provided worked examples, solve the new problem step by step, and end with a final line formatted exactly as `Final Answer: \\boxed{...}`."""

    SYSTEM_EXAMPLES_TEMPLATE = """{base_instruction}

Worked Examples:
{examples}"""

    USER_TEMPLATE = """Problem:
{problem}

Please follow the example style, reason step by step, and end with a final line formatted exactly as `Final Answer: \\boxed{{...}}`."""

    @property
    def name(self) -> str:
        return "cot_few_shot"

    def _format_examples(self, dataset_name: str | None) -> str:
        examples = get_few_shot_examples(dataset_name)
        max_examples = int(self.config.get("num_examples", 3))
        rendered = []
        for index, (question, answer) in enumerate(examples[:max_examples], start = 1):
            rendered.append(f"Example {index}\nQuestion: {question}\nSolution:\n{answer}")
        return "\n\n".join(rendered)

    def build_system_prompt(self, problem: str, **kwargs) -> str:
        dataset_name = kwargs.get("dataset_name")
        base_instruction = str(kwargs.get("system_prompt") or self.config.get("system_prompt") or self.DEFAULT_SYSTEM_PROMPT)
        return self.SYSTEM_EXAMPLES_TEMPLATE.format(
            base_instruction = base_instruction,
            examples = self._format_examples(dataset_name),
        )

    def build_user_prompt(self, problem: str, **kwargs) -> str:
        return self.USER_TEMPLATE.format(problem = problem)
