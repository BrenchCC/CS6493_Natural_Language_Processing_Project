"""
Base interfaces for prompting methods.
"""

from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import Dict


class PromptMethod(ABC):
    """
    Base class for all prompt methods.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize a prompt method.

        Args:
            config: Method-level configuration dictionary.
        """
        self.config = config or {}

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Return method name.

        Args:
            None.
        """

    def build_prompt(self, problem: str, **kwargs: Any) -> str:
        """
        Build model input prompt.

        Args:
            problem: Input math problem.
            **kwargs: Extra prompt context.
        """
        raise NotImplementedError

    def decode_strategy(self) -> Dict[str, Any]:
        """
        Return decoding parameters for this method.

        Args:
            None.
        """
        return {
            "temperature": self.config.get("temperature", 0.0),
            "top_p": self.config.get("top_p", 1.0),
            "max_tokens": self.config.get("max_tokens", 1024)
        }

    def post_process(self, raw_text: str, **kwargs: Any) -> str:
        """
        Post-process model output text.

        Args:
            raw_text: Raw generated text.
            **kwargs: Extra post-processing context.
        """
        return raw_text.strip()
