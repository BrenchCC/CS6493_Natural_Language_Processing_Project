"""Chain-of-Thought zero-shot prompting."""

from .base import PromptMethod


class CoTZero(PromptMethod):
    """Zero-shot CoT prompting."""

    DEFAULT_SYSTEM_PROMPT = """You are a careful mathematical reasoning assistant. Solve math problems step by step, keep the reasoning concise but complete, and present the final answer in \\boxed{}."""

    USER_TEMPLATE = """Problem:
{problem}

Please reason step by step and conclude with the final answer in \\boxed{{}}."""

    @property
    def name(self) -> str:
        return "cot_zero"

    def build_system_prompt(self, problem: str, **kwargs) -> str:
        return str(kwargs.get("system_prompt") or self.config.get("system_prompt") or self.DEFAULT_SYSTEM_PROMPT)

    def build_user_prompt(self, problem: str, **kwargs) -> str:
        """Format problem with zero-shot CoT instructions."""
        return self.USER_TEMPLATE.format(problem = problem)
