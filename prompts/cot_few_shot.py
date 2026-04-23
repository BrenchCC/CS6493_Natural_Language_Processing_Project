"""Few-shot CoT prompting."""

from .base import PromptMethod
from .few_shot_examples import get_examples


class CoTFewShot(PromptMethod):
    """Few-shot CoT prompting with dataset-aware exemplars."""

    DEFAULT_SYSTEM_PROMPT = """You are a careful mathematical reasoning assistant. Follow the style of the provided worked examples, solve the new problem step by step, and present the final answer in \\boxed{}."""

    USER_TEMPLATE = """Worked Examples:
{examples}

Problem:
{problem}

Please follow the example style, reason step by step, and end with the final answer in \\boxed{{}}."""

    @property
    def name(self) -> str:
        return "cot_few_shot"

    def _example_key(self, dataset_name: str | None) -> str:
        dataset_name = (dataset_name or "").lower()
        if "gsm" in dataset_name:
            return "gsm8k"
        return "math"

    def _format_examples(self, dataset_name: str | None) -> str:
        examples = get_examples().get(self._example_key(dataset_name), [])
        max_examples = int(self.config.get("num_examples", 3))
        rendered = []
        for index, (question, answer) in enumerate(examples[:max_examples], start = 1):
            rendered.append(f"Example {index}\nQuestion: {question}\nAnswer: {answer}")
        return "\n\n".join(rendered)

    def build_system_prompt(self, problem: str, **kwargs) -> str:
        return str(kwargs.get("system_prompt") or self.config.get("system_prompt") or self.DEFAULT_SYSTEM_PROMPT)

    def build_user_prompt(self, problem: str, **kwargs) -> str:
        dataset_name = kwargs.get("dataset_name")
        return self.USER_TEMPLATE.format(
            examples = self._format_examples(dataset_name),
            problem = problem,
        )
