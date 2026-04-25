"""Plan-and-Solve prompting."""

from .base import PromptMethod


class PlanAndSolve(PromptMethod):
    """Generate a short plan first, then solve following the plan."""

    PLAN_SYSTEM_PROMPT = (
        "You are a careful mathematical planner. Break the problem into a very short "
        "sequence of helpful steps before solving it."
    )

    PLAN_USER_TEMPLATE = """Problem:
{problem}

Create a concise plan with at most {max_plan_steps} numbered steps.
Keep each step short and actionable.
Do not solve the problem yet and do not give the final answer."""

    SOLVE_SYSTEM_PROMPT = (
        "You are a careful mathematical reasoning assistant. Follow the provided plan, "
        "solve the problem accurately, and end with a final line formatted exactly as "
        "`Final Answer: \\boxed{...}`."
    )

    SOLVE_USER_TEMPLATE = """Problem:
{problem}

Plan:
{plan}

Follow the plan to solve the problem step by step.
Keep the reasoning concise but complete.
End with a final line formatted exactly as `Final Answer: \\boxed{{...}}`."""

    def __init__(self, config: dict = None):
        super().__init__(config)
        self.max_plan_steps = int(self.config.get("max_plan_steps", 3))

    @property
    def name(self) -> str:
        return "plan_solve"

    @property
    def run_mode(self) -> str:
        return "multi_pass"

    def build_system_prompt(self, problem: str, **kwargs) -> str:
        return str(kwargs.get("system_prompt") or self.config.get("system_prompt") or self.PLAN_SYSTEM_PROMPT)

    def build_user_prompt(self, problem: str, **kwargs) -> str:
        return self.PLAN_USER_TEMPLATE.format(problem = problem, max_plan_steps = self.max_plan_steps)

    def _build_stage_messages(self, system_prompt: str, user_prompt: str) -> list[dict[str, str]]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})
        return messages

    def format_solve_prompt(self, problem: str, plan: str) -> str:
        return self.SOLVE_USER_TEMPLATE.format(problem = problem, plan = plan.strip() or "1. Solve the problem carefully.")

    def run(self, engine, sample, **kwargs):
        problem = str(sample.get("question", ""))
        steps = []
        decode_strategy = self.resolve_decode_strategy(**kwargs)

        plan_messages = self.build_messages(problem = problem, sample = sample, **kwargs)
        plan_outputs = engine.chat(messages = plan_messages, **decode_strategy)
        plan_text = plan_outputs[0] if plan_outputs else ""
        steps.append({"stage": "plan", "messages": plan_messages, "response": plan_text})

        solve_messages = self._build_stage_messages(
            system_prompt = self.SOLVE_SYSTEM_PROMPT,
            user_prompt = self.format_solve_prompt(problem = problem, plan = plan_text),
        )
        solve_outputs = engine.chat(messages = solve_messages, **decode_strategy)
        final_solution = solve_outputs[0] if solve_outputs else ""
        steps.append({"stage": "solve", "messages": solve_messages, "response": final_solution})

        return {
            "input_messages": plan_messages,
            "raw_response": final_solution,
            "final_response": self.post_process(final_solution, sample = sample, **kwargs),
            "intermediate_outputs": steps,
            "metadata": {
                "run_mode": self.run_mode,
                "max_plan_steps": self.max_plan_steps,
                "decode_strategy": decode_strategy,
            },
        }
