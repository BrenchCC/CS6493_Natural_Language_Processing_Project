"""
Self-consistency prompting method.
"""

import math
from collections import Counter
from typing import Any
from typing import Dict
from typing import List

from .base import PromptMethod


class SelfConsistency(PromptMethod):
    """
    Self-consistency prompting with n-way sampling and majority voting.
    """

    TEMPLATE = (
        "Solve the following math problem step by step. "
        "Show concise reasoning, then provide final answer in \\boxed{{}}.\\n\\n"
        "Problem:\\n{problem}\\n\\n"
        "Reasoning:"
    )

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize self-consistency method.

        Args:
            config: Method-level configuration dictionary.
        """
        super().__init__(config = config)
        cfg = config or {}
        self.n_samples = int(cfg.get("n_samples", 5))

    @property
    def name(self) -> str:
        """
        Return method name.

        Args:
            None.
        """
        return "self_consistency"

    def build_prompt(self, problem: str, **kwargs: Any) -> str:
        """
        Build prompt text.

        Args:
            problem: Input math problem.
            **kwargs: Extra prompt context.
        """
        return self.TEMPLATE.format(problem = problem)

    def decode_strategy(self) -> Dict[str, Any]:
        """
        Return decoding parameters for self-consistency.

        Args:
            None.
        """
        params = super().decode_strategy()
        if params.get("temperature", 0.0) <= 0.0:
            params["temperature"] = 0.7
        return params

    def aggregate(
        self,
        responses: List[str],
        answers: List[str]
    ) -> Dict[str, Any]:
        """
        Aggregate sampled answers using majority vote.

        Args:
            responses: Raw responses from each sample.
            answers: Extracted final answer strings.
        """
        counter = Counter(answers)
        if not counter:
            return {
                "final_answer": "",
                "vote_count": 0,
                "vote_ratio": 0.0,
                "vote_entropy": 0.0,
                "responses": responses,
                "answers": answers
            }

        final_answer, vote_count = counter.most_common(1)[0]
        total = max(1, len(answers))
        vote_ratio = vote_count / total

        vote_entropy = 0.0
        for count in counter.values():
            prob = count / total
            vote_entropy -= prob * math.log(prob)

        return {
            "final_answer": final_answer,
            "vote_count": vote_count,
            "vote_ratio": vote_ratio,
            "vote_entropy": vote_entropy,
            "responses": responses,
            "answers": answers
        }
