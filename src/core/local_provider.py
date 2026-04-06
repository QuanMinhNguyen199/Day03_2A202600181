import os
import time
from typing import Any, Dict, Generator, Optional

from llama_cpp import Llama

from src.core.llm_provider import LLMProvider


class LocalProvider(LLMProvider):
    """
    LLM Provider for local models using llama-cpp-python.
    Optimized for CPU usage with GGUF models.
    """

    def __init__(self, model_path: str, n_ctx: int = 2048, n_threads: Optional[int] = None):
        super().__init__(model_name=os.path.basename(model_path))

        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Model file not found at {model_path}. Please download it first."
            )

        self.llm = Llama(
            model_path=model_path,
            n_ctx=n_ctx,
            n_threads=n_threads,
            n_gpu_layers=0,
            verbose=False,
        )

    def _build_prompt(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if system_prompt:
            return (
                f"<|system|>\n{system_prompt}<|end|>\n"
                f"<|user|>\n{prompt}<|end|>\n"
                f"<|assistant|>\n"
            )
        return f"<|user|>\n{prompt}<|end|>\n<|assistant|>\n"

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        start_time = time.time()
        full_prompt = self._build_prompt(prompt, system_prompt)

        response = self.llm(
            full_prompt,
            max_tokens=384,
            temperature=0.1,
            top_p=0.95,
            repeat_penalty=1.05,
            stop=["<|end|>", "Observation:"],
            echo=False,
        )

        end_time = time.time()
        latency_ms = int((end_time - start_time) * 1000)

        usage_raw = response.get("usage", {})
        content = response["choices"][0]["text"].strip()

        return {
            "content": content,
            "usage": {
                "prompt_tokens": usage_raw.get("prompt_tokens", 0),
                "completion_tokens": usage_raw.get("completion_tokens", 0),
                "total_tokens": usage_raw.get("total_tokens", 0),
            },
            "latency_ms": latency_ms,
            "provider": "local",
        }

    def stream(self, prompt: str, system_prompt: Optional[str] = None) -> Generator[str, None, None]:
        full_prompt = self._build_prompt(prompt, system_prompt)

        stream = self.llm(
            full_prompt,
            max_tokens=384,
            temperature=0.1,
            top_p=0.95,
            repeat_penalty=1.05,
            stop=["<|end|>", "Observation:"],
            stream=True,
        )

        for chunk in stream:
            token = chunk["choices"][0]["text"]
            if token:
                yield token