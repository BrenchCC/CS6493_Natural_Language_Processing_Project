"""Tool-Integrated Reasoning prompting."""

from .base import PromptMethod


class ToolIntegratedReasoning(PromptMethod):
    """Prompt the model to interleave reasoning with Python snippets."""

    DEFAULT_SYSTEM_PROMPT = """You are a mathematical reasoning assistant that can mix natural-language reasoning with Python snippets. Use Python only when it helps computation, wrap code in ```python``` fences, wrap execution results in ```output``` fences when needed, and present the final answer in \\boxed{}."""

    USER_TEMPLATE = """Problem:
{problem}

Please solve the problem step by step. Use Python code blocks only when useful, and conclude with the final answer in \\boxed{{}}."""

    @property
    def name(self) -> str:
        return "tir"

    def build_system_prompt(self, problem: str, **kwargs) -> str:
        return str(kwargs.get("system_prompt") or self.config.get("system_prompt") or self.DEFAULT_SYSTEM_PROMPT)

    def build_user_prompt(self, problem: str, **kwargs) -> str:
        return self.USER_TEMPLATE.format(problem = problem)
