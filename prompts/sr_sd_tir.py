"""
Skill-routed self-discover TIR prompting method.
"""

from typing import Any
from typing import Dict

from .base import PromptMethod


class SkillRoutedSelfDiscoverTIR(PromptMethod):
    """
    Three-stage method: plan, solve-with-tools, and reflect.
    """

    PLAN_TEMPLATE = (
        "You are solving a hard math question.\\n"
        "First produce a compact plan with 2-4 steps, each step focused on one sub-goal.\\n"
        "Do not solve yet.\\n\\n"
        "Question: {problem}\\n\\n"
        "Plan:"
    )

    SOLVE_TEMPLATE = (
        "Follow the plan and solve the problem using tool-integrated reasoning.\\n"
        "When needed, write executable Python code in ```python blocks and use exact symbolic math.\\n"
        "Use execution feedback if available.\\n"
        "End with final answer in \\boxed{{}}.\\n\\n"
        "Question: {problem}\\n\\n"
        "Plan:\\n{plan}\\n\\n"
        "Solution:"
    )

    REFLECT_TEMPLATE = (
        "Review the current solution for logical errors, arithmetic errors, or unnecessary extra reasoning.\\n"
        "If the answer is already correct, keep it concise and stop.\\n"
        "Return the corrected final answer in \\boxed{{}}.\\n\\n"
        "Question: {problem}\\n\\n"
        "Current solution:\\n{solution}\\n\\n"
        "Refined solution:"
    )

    @property
    def name(self) -> str:
        """
        Return method name.

        Args:
            None.
        """
        return "sr_sd_tir"

    def build_prompt(self, problem: str, **kwargs: Any) -> str:
        """
        Build stage-1 planning prompt.

        Args:
            problem: Input math problem.
            **kwargs: Extra prompt context.
        """
        return self.PLAN_TEMPLATE.format(problem = problem)

    def build_solve_prompt(self, problem: str, plan: str) -> str:
        """
        Build stage-2 solving prompt.

        Args:
            problem: Input math problem.
            plan: Stage-1 generated plan text.
        """
        return self.SOLVE_TEMPLATE.format(problem = problem, plan = plan)

    def build_reflect_prompt(self, problem: str, solution: str) -> str:
        """
        Build stage-3 reflection prompt.

        Args:
            problem: Input math problem.
            solution: Stage-2 generated solution text.
        """
        return self.REFLECT_TEMPLATE.format(problem = problem, solution = solution)

    def decode_strategy(self) -> Dict[str, Any]:
        """
        Return decoding parameters for SR-SD-TIR.

        Args:
            None.
        """
        params = super().decode_strategy()
        params["temperature"] = self.config.get("temperature", 0.2)
        return params
