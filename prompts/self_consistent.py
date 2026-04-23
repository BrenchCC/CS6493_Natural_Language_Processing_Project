"""Self-Consistency prompting."""

from collections import Counter
from typing import Optional

from .base import PromptMethod


class SelfConsistency(PromptMethod):
    """Sample multiple CoT responses and aggregate final answers."""

    DEFAULT_SYSTEM_PROMPT = """You are a mathematical reasoning assistant. Produce a full step-by-step solution and give the final answer in \\boxed{}. Different attempts may explore different valid paths, but each attempt must remain self-consistent."""

    USER_TEMPLATE = """Problem:
{problem}

Please solve it step by step and conclude with the final answer in \\boxed{{}}."""

    def __init__(self, config: dict = None):
        super().__init__(config)
        self.n_samples = config.get("n_samples", 5) if config else 5

    @property
    def name(self) -> str:
        return "self_consistency"

    @property
    def run_mode(self) -> str:
        return "sample_aggregate"

    def build_system_prompt(self, problem: str, **kwargs) -> str:
        return str(kwargs.get("system_prompt") or self.config.get("system_prompt") or self.DEFAULT_SYSTEM_PROMPT)

    def build_user_prompt(self, problem: str, **kwargs) -> str:
        """Format the shared prompt for self-consistency sampling."""
        return self.USER_TEMPLATE.format(problem = problem)

    def aggregate(self, responses: list, answers: Optional[list] = None) -> str:
        """Aggregate multiple responses via majority vote."""
        if answers is None:
            answers = responses

        counter = Counter(answers)
        most_common = counter.most_common(1)
        if not most_common:
            return ""
        return most_common[0][0]

    def run(self, engine, sample, **kwargs):
        from evaluation.parser import extract_answer

        messages = self.build_messages(problem = str(sample.get("question", "")), sample = sample, **kwargs)
        decode_strategy = self.decode_strategy()
        if "enable_thinking" in kwargs:
            decode_strategy["enable_thinking"] = kwargs.get("enable_thinking")
        sample_count = max(1, int(self.n_samples))
        responses = []
        answers = []

        for _ in range(sample_count):
            raw_text = engine.chat(messages = messages, **decode_strategy)
            response_text = raw_text[0] if raw_text else ""
            responses.append(response_text)
            answers.append(extract_answer(response_text, kwargs.get("dataset_name", "math")))

        voted_answer = self.aggregate(responses = responses, answers = answers)
        selected_index = 0
        for index, answer in enumerate(answers):
            if answer == voted_answer:
                selected_index = index
                break

        raw_response = responses[selected_index] if responses else ""
        return {
            "input_messages": messages,
            "raw_response": raw_response,
            "final_response": self.post_process(raw_response, sample = sample, **kwargs),
            "intermediate_outputs": [
                {
                    "sample_index": index,
                    "raw_response": response,
                    "parsed_answer": answers[index],
                }
                for index, response in enumerate(responses)
            ],
            "metadata": {
                "run_mode": self.run_mode,
                "n_samples": sample_count,
                "aggregated_answer": voted_answer,
            },
        }
