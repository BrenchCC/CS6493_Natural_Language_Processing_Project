"""
Self-Refine prompting.
Generates an initial solution, then iteratively critiques and refines it.
"""

from .base import PromptMethod


class SelfRefine(PromptMethod):
    """
    Self-Refine prompting.

    Three-phase process:
    1. Solve: Generate an initial solution.
    2. Critique: Identify errors or weaknesses in the solution.
    3. Refine: Produce an improved solution based on the critique.
    """

    SOLVE_TEMPLATE = """Solve the following math problem step by step. Show your reasoning clearly and put your final answer in \\boxed{{}}.

Problem:
{problem}

Please provide your solution:"""

    CRITIQUE_TEMPLATE = """Review the following solution to a math problem. Identify any errors in reasoning, calculation mistakes, or logical flaws. Be specific about what is wrong and why.

Problem:
{problem}

Solution to review:
{solution}

Please provide your critique:"""

    REFINE_TEMPLATE = """Based on the critique below, improve the solution to the following math problem. Fix any identified errors and provide the corrected solution. Put your final answer in \\boxed{{}}.

Problem:
{problem}

Original solution:
{solution}

Critique:
{critique}

Please provide the improved solution:"""

    def __init__(self, config: dict = None):
        super().__init__(config)
        self.max_rounds = config.get("max_refine_rounds", 2) if config else 2

    @property
    def name(self) -> str:
        return "self_refine"

    @property
    def is_multi_pass(self) -> bool:
        return True

    def format(self, problem: str, **kwargs) -> str:
        """
        Format initial solve prompt.

        Args:
            problem: The math problem text.
        """
        return self.SOLVE_TEMPLATE.format(problem=problem)

    def format_critique(self, problem: str, solution: str) -> str:
        """
        Format critique request given problem and initial solution.

        Args:
            problem: The original math problem.
            solution: The model's initial solution text.
        """
        return self.CRITIQUE_TEMPLATE.format(problem=problem, solution=solution)

    def format_refine(self, problem: str, solution: str, critique: str) -> str:
        """
        Format refinement request.

        Args:
            problem: The original math problem.
            solution: The current solution text.
            critique: The critique of the solution.
        """
        return self.REFINE_TEMPLATE.format(
            problem=problem, solution=solution, critique=critique
        )