"""API-backed inference engine with the same interface as VLLMEngine."""

from __future__ import annotations

import os
import sys
import threading
from typing import Any
from typing import Dict
from typing import List

# Add project root to Python path
sys.path.append(os.getcwd())

from api_server.llm_server import LLM_Client
from api_server.slidingwindow import _SlidingWindowRateLimiter


class APIEngine:
    """Chat engine that calls an Ark endpoint from environment variables.

    Args:
        mode: API provider mode. This project uses `ark` for API experiments.
        api_key_env: Environment variable containing the API key.
        base_url_env: Environment variable containing the API base URL.
        model_env: Environment variable containing the active Ark endpoint.
        identifier_env: Environment variable containing a human-readable model identifier.
        timeout: Request timeout in seconds.
        print_stream: Whether the underlying client should print streaming tokens.
        rpm: Maximum requests per sliding window. Non-positive values disable request limiting.
        tpm: Maximum reserved tokens per sliding window. Non-positive values disable token limiting.
        window_s: Sliding window length in seconds.
    """

    def __init__(
        self,
        mode: str = "ark",
        api_key_env: str = "LLM_API_KEY",
        base_url_env: str = "LLM_API_BASE_URL",
        model_env: str = "LLM_MODEL",
        identifier_env: str = "LLM_IDENTIFIER",
        timeout: int = 300,
        print_stream: bool = False,
        rpm: int = 0,
        tpm: int = 0,
        window_s: float = 60.0,
    ) -> None:
        self.mode = mode
        self.api_key_env = api_key_env
        self.base_url_env = base_url_env
        self.model_env = model_env
        self.identifier_env = identifier_env
        self.timeout = timeout
        self.print_stream = print_stream
        self.rpm = int(rpm)
        self.tpm = int(tpm)
        self.window_s = float(window_s)
        self._thread_local = threading.local()
        self._rate_limiter = _SlidingWindowRateLimiter(
            rpm = self.rpm,
            tpm = self.tpm,
            window_s = self.window_s,
        )

        self.endpoint = os.environ.get(self.model_env, "").strip()
        self.identifier = os.environ.get(self.identifier_env, "").strip()
        if not self.endpoint:
            raise RuntimeError(f"Missing active API endpoint in `{self.model_env}`.")

    def start_call_trace(self) -> None:
        """Start collecting API call metadata for the current thread."""
        self._thread_local.call_trace = []

    def consume_call_trace(self) -> List[Dict[str, Any]]:
        """Return and clear collected API call metadata for the current thread."""
        call_trace = getattr(self._thread_local, "call_trace", [])
        self._thread_local.call_trace = []
        return list(call_trace)

    def _append_call_trace(self, call_metadata: Dict[str, Any]) -> None:
        """Append one API call metadata record when tracing is enabled.

        Args:
            call_metadata: Non-secret metadata for one API generation call.
        """
        call_trace = getattr(self._thread_local, "call_trace", None)
        if isinstance(call_trace, list):
            call_metadata = dict(call_metadata)
            call_metadata["call_index"] = len(call_trace) + 1
            call_trace.append(call_metadata)

    def _get_client(self) -> LLM_Client:
        """Return a per-thread API client for concurrent inference."""
        client = getattr(self._thread_local, "client", None)
        if client is not None:
            return client

        client = LLM_Client(
            mode = self.mode,
            api_key = os.environ.get(self.api_key_env),
            base_url = os.environ.get(self.base_url_env),
            default_model = self.endpoint,
            timeout = self.timeout,
            print_stream = self.print_stream,
        )
        self._thread_local.client = client
        return client

    def _estimate_reserved_tokens(self, messages: List[Dict[str, str]], max_tokens: int | None) -> int:
        """Estimate total request tokens for sliding-window throttling."""
        input_text = "\n".join(str(message.get("content", "")) for message in messages)
        input_tokens = _SlidingWindowRateLimiter.estimate_tokens_text(input_text)
        output_tokens = int(max_tokens or 0)
        return max(1, input_tokens + max(0, output_tokens))

    def describe(self) -> Dict[str, Any]:
        """Return non-secret runtime metadata for logging and summaries."""
        return {
            "backend": "api",
            "api_mode": self.mode,
            "api_identifier": self.identifier,
            "api_model_env": self.model_env,
            "api_base_url_env": self.base_url_env,
            "api_rpm": self.rpm,
            "api_tpm": self.tpm,
            "api_window_s": self.window_s,
        }

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float | None = None,
        top_p: float | None = None,
        max_tokens: int | None = None,
        enable_thinking: bool | str | Dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> List[str]:
        """Generate one response from OpenAI-style chat messages.

        Args:
            messages: OpenAI-style chat messages.
            temperature: Sampling temperature.
            top_p: Nucleus sampling probability.
            max_tokens: Maximum generated tokens.
            enable_thinking: Ark thinking toggle or custom thinking payload.
            **kwargs: Additional decode fields; vLLM-only fields are ignored.
        """
        extra_body = kwargs.get("extra_body")
        timeout = kwargs.get("timeout")
        reserve_tokens = self._estimate_reserved_tokens(messages = messages, max_tokens = max_tokens)
        self._rate_limiter.acquire(reserve_tokens = reserve_tokens)
        reasoning_content, result, prompt_tokens, completion_tokens, usage_metadata = self._get_client().chat(
            input_query = "",
            end_point = self.endpoint,
            messages = messages,
            stream = False,
            reasoning_option = enable_thinking,
            temperature = temperature,
            top_p = top_p,
            max_tokens = max_tokens,
            extra_body = extra_body,
            timeout = timeout,
        )
        response_text = result if isinstance(result, str) else ""
        reasoning_text = reasoning_content if isinstance(reasoning_content, str) else ""
        call_metadata = {
            "reasoning_content": reasoning_text,
            "reasoning_content_chars": len(reasoning_text),
            "estimated_reasoning_tokens": len(reasoning_text.strip().split()) if reasoning_text.strip() else 0,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "usage": usage_metadata.get("usage", {}) if isinstance(usage_metadata, dict) else {},
            "reasoning_tokens": usage_metadata.get("reasoning_tokens", "") if isinstance(usage_metadata, dict) else "",
            "total_tokens": usage_metadata.get("total_tokens", "") if isinstance(usage_metadata, dict) else "",
            "response_length_chars": len(response_text),
        }
        self._append_call_trace(call_metadata = call_metadata)
        return [response_text]
