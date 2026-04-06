import time
import warnings
from typing import Any, Dict, Generator, Optional

# Suppress FutureWarning from deprecated SDK
warnings.filterwarnings("ignore", category=FutureWarning, module="google")
import google.generativeai as genai

from src.core.llm_provider import LLMProvider


class GeminiProvider(LLMProvider):
    def __init__(self, model_name: str = "gemini-2.0-flash", api_key: Optional[str] = None):
        super().__init__(model_name, api_key)
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required. Set it in .env file.")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name)

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        start_time = time.time()

        full_prompt = prompt
        if system_prompt:
            full_prompt = f"System:\n{system_prompt}\n\nUser:\n{prompt}"

        try:
            response = self.model.generate_content(full_prompt)
        except Exception as exc:
            return {
                "content": f"[LLM Error] {exc}",
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                "latency_ms": int((time.time() - start_time) * 1000),
                "provider": "google",
            }

        end_time = time.time()
        latency_ms = int((end_time - start_time) * 1000)

        usage_meta = getattr(response, "usage_metadata", None)

        return {
            "content": getattr(response, "text", "") or "",
            "usage": {
                "prompt_tokens": getattr(usage_meta, "prompt_token_count", 0) if usage_meta else 0,
                "completion_tokens": getattr(usage_meta, "candidates_token_count", 0) if usage_meta else 0,
                "total_tokens": getattr(usage_meta, "total_token_count", 0) if usage_meta else 0,
            },
            "latency_ms": latency_ms,
            "provider": "google",
        }

    def stream(self, prompt: str, system_prompt: Optional[str] = None) -> Generator[str, None, None]:
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"System:\n{system_prompt}\n\nUser:\n{prompt}"

        response = self.model.generate_content(full_prompt, stream=True)
        for chunk in response:
            text = getattr(chunk, "text", "")
            if text:
                yield text