"""Base interfaces for prompting methods."""

from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import Dict
from typing import List


class PromptMethod(ABC):
    """Base class for all prompt methods."""

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
        """Return method name."""

    @property
    def run_mode(self) -> str:
        """Return method execution mode."""
        return "single_pass"

    def build_system_prompt(self, problem: str, **kwargs: Any) -> str:
        """Build the system instruction for the method."""
        return str(kwargs.get("system_prompt") or self.config.get("system_prompt") or "")

    @abstractmethod
    def build_user_prompt(self, problem: str, **kwargs: Any) -> str:
        """Build the user message for the method."""

    def build_prompt(self, problem: str, **kwargs: Any) -> str:
        """Backward-compatible alias for the user prompt body."""
        return self.build_user_prompt(problem = problem, **kwargs)

    def build_messages(self, problem: str, **kwargs: Any) -> List[Dict[str, str]]:
        """Build OpenAI-style chat messages for the model."""
        system_prompt = self.build_system_prompt(problem = problem, **kwargs)
        user_prompt = self.build_user_prompt(problem = problem, **kwargs)
        messages: List[Dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": str(system_prompt)})
        messages.append({"role": "user", "content": user_prompt})
        return messages

    def decode_strategy(self) -> Dict[str, Any]:
        """Return decoding parameters for this method."""
        decode: Dict[str, Any] = {
            "temperature": self.config.get("temperature", 0.7),
            "top_p": self.config.get("top_p", 0.7),
            "max_tokens": self.config.get("max_tokens", 4096)
        }

        # Optional sampling controls passed through to vLLM SamplingParams.
        if "repetition_penalty" in self.config:
            decode["repetition_penalty"] = float(self.config["repetition_penalty"])
        return decode

    def resolve_decode_strategy(self, **kwargs: Any) -> Dict[str, Any]:
        """Return decoding parameters after applying runtime overrides."""
        decode_strategy = dict(self.decode_strategy())
        model_settings = kwargs.get("model_settings") or {}
        requested_enable_thinking = kwargs.get("enable_thinking") if "enable_thinking" in kwargs else None
        if model_settings.get("cannot_disable_thinking", False):
            requested_enable_thinking = None
        if "enable_thinking" in kwargs or requested_enable_thinking is not None:
            decode_strategy["enable_thinking"] = requested_enable_thinking

        disable_sampling = bool(kwargs.get("disable_sampling", model_settings.get("disable_sampling", False)))
        if disable_sampling:
            decode_strategy["temperature"] = 0.0
            decode_strategy["top_p"] = 1.0
        return decode_strategy

    def post_process(self, raw_text: str, **kwargs: Any) -> str:
        """Post-process model output text."""
        return raw_text.strip()

    def run(self, engine: Any, sample: Dict[str, Any], **kwargs: Any) -> Dict[str, Any]:
        """Execute this prompting method against one sample."""
        problem = str(sample.get("question", ""))
        messages = self.build_messages(problem = problem, sample = sample, **kwargs)
        decode_strategy = self.resolve_decode_strategy(**kwargs)
        responses = engine.chat(messages = messages, **decode_strategy)
        raw_response = responses[0] if responses else ""
        final_response = self.post_process(raw_response, sample = sample, **kwargs)
        return {
            "input_messages": messages,
            "raw_response": raw_response,
            "final_response": final_response,
            "intermediate_outputs": [],
            "metadata": {
                "run_mode": self.run_mode,
                "decode_strategy": decode_strategy,
            },
        }
