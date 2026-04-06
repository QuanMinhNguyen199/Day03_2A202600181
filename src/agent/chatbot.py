from src.core.llm_provider import LLMProvider
from src.telemetry.logger import logger
from src.telemetry.metrics import tracker


class BaselineChatbot:
    def __init__(self, llm: LLMProvider):
        self.llm = llm

    def chat(self, user_input: str) -> str:
        system_prompt = (
            "Bạn là chatbot tư vấn vé xem phim. "
            "Trả lời trực tiếp bằng tiếng Việt, không gọi tool, không mô phỏng hành động đặt vé."
        )
        result = self.llm.generate(user_input, system_prompt=system_prompt)

        tracker.track_request(
            provider=result.get("provider", "unknown"),
            model=self.llm.model_name,
            usage=result.get("usage", {}),
            latency_ms=result.get("latency_ms", 0),
        )

        logger.log_event("CHATBOT_RESPONSE", {
            "input": user_input,
            "output": result.get("content", ""),
            "usage": result.get("usage", {}),
            "latency_ms": result.get("latency_ms", 0),
        })

        return result.get("content", "")