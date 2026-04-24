"""Self-Refine prompting."""

from .base import PromptMethod


class SelfRefine(PromptMethod):
    """Solve, critique, and refine a solution iteratively."""

    SOLVE_SYSTEM_PROMPT = """You are a careful mathematical reasoning assistant. Solve the problem step by step and present the final answer in \\boxed{}."""

    SOLVE_USER_TEMPLATE = """Problem:
{problem}

Please provide a complete step-by-step solution."""

    CRITIQUE_SYSTEM_PROMPT = """You are a strict mathematical reviewer. Inspect the provided solution, identify reasoning or calculation errors, and explain them precisely."""

    CRITIQUE_USER_TEMPLATE = """Problem:
{problem}

Solution to review:
{solution}

Please provide a concise but specific critique."""

    REFINE_SYSTEM_PROMPT = """You are a mathematical editor. Revise the solution using the critique, fix all identified issues, and present the corrected final answer in \\boxed{}."""

    REFINE_USER_TEMPLATE = """Problem:
{problem}

Original solution:
{solution}

Critique:
{critique}

Please provide the improved step-by-step solution."""

    def __init__(self, config: dict = None):
        super().__init__(config)
        self.max_rounds = config.get("max_refine_rounds", 2) if config else 2

    @property
    def name(self) -> str:
        return "self_refine"

    @property
    def run_mode(self) -> str:
        return "multi_pass"

    def build_system_prompt(self, problem: str, **kwargs) -> str:
        return str(kwargs.get("system_prompt") or self.config.get("system_prompt") or self.SOLVE_SYSTEM_PROMPT)

    def build_user_prompt(self, problem: str, **kwargs) -> str:
        """Format the initial solve prompt."""
        return self.SOLVE_USER_TEMPLATE.format(problem = problem)

    def _build_stage_messages(self, system_prompt: str, user_prompt: str) -> list[dict[str, str]]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})
        return messages

    def format_critique(self, problem: str, solution: str) -> str:
        """Format critique request given problem and initial solution."""
        return self.CRITIQUE_USER_TEMPLATE.format(problem = problem, solution = solution)

    def format_refine(self, problem: str, solution: str, critique: str) -> str:
        """Format refinement request."""
        return self.REFINE_USER_TEMPLATE.format(problem = problem, solution = solution, critique = critique)

    def run(self, engine, sample, **kwargs):
        problem = str(sample.get("question", ""))
        steps = []
        decode_strategy = self.resolve_decode_strategy(**kwargs)
        solve_messages = self.build_messages(problem = problem, sample = sample, **kwargs)
        solve_outputs = engine.chat(messages = solve_messages, **decode_strategy)
        current_solution = solve_outputs[0] if solve_outputs else ""
        steps.append({"stage": "solve", "messages": solve_messages, "response": current_solution})

        rounds = max(1, int(self.max_rounds))
        for round_index in range(rounds):
            critique_prompt = self.format_critique(problem = problem, solution = current_solution)
            critique_messages = self._build_stage_messages(
                system_prompt = self.CRITIQUE_SYSTEM_PROMPT,
                user_prompt = critique_prompt,
            )
            critique_outputs = engine.chat(messages = critique_messages, **decode_strategy)
            critique = critique_outputs[0] if critique_outputs else ""
            steps.append(
                {
                    "stage": f"critique_{round_index + 1}",
                    "messages": critique_messages,
                    "response": critique,
                }
            )

            refine_prompt = self.format_refine(problem = problem, solution = current_solution, critique = critique)
            refine_messages = self._build_stage_messages(
                system_prompt = self.REFINE_SYSTEM_PROMPT,
                user_prompt = refine_prompt,
            )
            refine_outputs = engine.chat(messages = refine_messages, **decode_strategy)
            current_solution = refine_outputs[0] if refine_outputs else ""
            steps.append(
                {
                    "stage": f"refine_{round_index + 1}",
                    "messages": refine_messages,
                    "response": current_solution,
                }
            )

        return {
            "input_messages": solve_messages,
            "raw_response": current_solution,
            "final_response": self.post_process(current_solution, sample = sample, **kwargs),
            "intermediate_outputs": steps,
            "metadata": {
                "run_mode": self.run_mode,
                "max_refine_rounds": rounds,
                "decode_strategy": decode_strategy,
            },
        }
