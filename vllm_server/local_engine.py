"""
Local vLLM engine wrapper for direct model loading.
"""

import threading
from typing import Any
from typing import Dict
from typing import List


class LocalVLLMEngine:
    """
    Thread-safe wrapper around vLLM LLM.generate.
    """

    def __init__(self, model_id: str, engine_config: Dict[str, Any]):
        """
        Initialize local vLLM engine.

        Args:
            model_id: Hugging Face model identifier.
            engine_config: vLLM runtime configuration.
        """
        try:
            from vllm import LLM
            from vllm import SamplingParams
        except ImportError as exc:
            raise ImportError(
                "vLLM is required for local inference. Install with `pip install vllm`."
            ) from exc

        self._sampling_params_cls = SamplingParams
        self._lock = threading.Lock()
        self.model_id = model_id

        cfg = engine_config or {}
        self.llm = LLM(
            model = model_id,
            tensor_parallel_size = int(cfg.get("tensor_parallel_size", 1)),
            dtype = cfg.get("dtype", "auto"),
            gpu_memory_utilization = float(cfg.get("gpu_memory_utilization", 0.9)),
            max_model_len = int(cfg.get("max_model_len", 4096)),
            max_num_seqs = int(cfg.get("max_num_seqs", 16)),
            trust_remote_code = bool(cfg.get("trust_remote_code", True))
        )

    def generate_batch(
        self,
        prompts: List[str],
        decode_config: Dict[str, Any]
    ) -> List[str]:
        """
        Generate texts for a batch of prompts.

        Args:
            prompts: Prompt list.
            decode_config: Sampling parameter dictionary.
        """
        sampling_params = self._sampling_params_cls(**decode_config)
        with self._lock:
            outputs = self.llm.generate(prompts, sampling_params = sampling_params)

        generated = []
        for item in outputs:
            if not item.outputs:
                generated.append("")
                continue
            generated.append(item.outputs[0].text)
        return generated

    def generate_text(self, prompt: str, decode_config: Dict[str, Any]) -> str:
        """
        Generate one text for a single prompt.

        Args:
            prompt: Prompt text.
            decode_config: Sampling parameter dictionary.
        """
        return self.generate_batch(
            prompts = [prompt],
            decode_config = decode_config
        )[0]
