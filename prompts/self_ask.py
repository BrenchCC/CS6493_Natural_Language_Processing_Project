"""Self-Ask prompting."""

from .base import PromptMethod


class SelfAsk(PromptMethod):
    """Ask intermediate questions before solving the original problem."""

    ASK_SYSTEM_PROMPT = (
        "You are a careful mathematical analyst. Before solving the main problem, "
        "identify the intermediate questions that matter most."
    )

    ASK_USER_TEMPLATE = """Problem:
{problem}

List up to {max_self_questions} short intermediate questions that would help solve this problem.
Only output numbered questions.
Do not answer them yet.
Do not provide the final answer yet."""

    ANSWER_SYSTEM_PROMPT = (
        "You are a careful mathematical reasoning assistant. Answer the intermediate "
        "questions briefly, then solve the original problem, and end with a final line "
        "formatted exactly as `Final Answer: \\boxed{...}`."
    )

    ANSWER_USER_TEMPLATE = """Problem:
{problem}

Intermediate questions:
{questions}

Answer each intermediate question briefly, then solve the original problem.
Use the format:
Q1: ...
A1: ...

Continue as needed, then end with a final line formatted exactly as `Final Answer: \\boxed{{...}}`."""

    def __init__(self, config: dict = None):
        super().__init__(config)
        self.max_self_questions = int(self.config.get("max_self_questions", 3))

    @property
    def name(self) -> str:
        return "self_ask"

    @property
    def run_mode(self) -> str:
        return "multi_pass"

    def build_system_prompt(self, problem: str, **kwargs) -> str:
        return str(kwargs.get("system_prompt") or self.config.get("system_prompt") or self.ASK_SYSTEM_PROMPT)

    def build_user_prompt(self, problem: str, **kwargs) -> str:
        return self.ASK_USER_TEMPLATE.format(problem = problem, max_self_questions = self.max_self_questions)

    def _build_stage_messages(self, system_prompt: str, user_prompt: str) -> list[dict[str, str]]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})
        return messages

    def format_answer_prompt(self, problem: str, questions: str) -> str:
        return self.ANSWER_USER_TEMPLATE.format(
            problem = problem,
            questions = questions.strip() or "1. What is the most direct way to solve the problem?",
        )

    def run(self, engine, sample, **kwargs):
        problem = str(sample.get("question", ""))
        steps = []
        decode_strategy = self.resolve_decode_strategy(**kwargs)

        ask_messages = self.build_messages(problem = problem, sample = sample, **kwargs)
        ask_outputs = engine.chat(messages = ask_messages, **decode_strategy)
        questions_text = ask_outputs[0] if ask_outputs else ""
        steps.append({"stage": "ask", "messages": ask_messages, "response": questions_text})

        answer_messages = self._build_stage_messages(
            system_prompt = self.ANSWER_SYSTEM_PROMPT,
            user_prompt = self.format_answer_prompt(problem = problem, questions = questions_text),
        )
        answer_outputs = engine.chat(messages = answer_messages, **decode_strategy)
        final_solution = answer_outputs[0] if answer_outputs else ""
        steps.append({"stage": "answer", "messages": answer_messages, "response": final_solution})

        return {
            "input_messages": ask_messages,
            "raw_response": final_solution,
            "final_response": self.post_process(final_solution, sample = sample, **kwargs),
            "intermediate_outputs": steps,
            "metadata": {
                "run_mode": self.run_mode,
                "max_self_questions": self.max_self_questions,
                "decode_strategy": decode_strategy,
            },
        }
