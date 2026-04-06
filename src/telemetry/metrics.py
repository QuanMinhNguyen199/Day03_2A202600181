from typing import Any, Dict, List

from src.telemetry.logger import logger


class PerformanceTracker:
    """Track token, latency, and estimated cost per LLM request."""

    def __init__(self):
        self.session_metrics: List[Dict[str, Any]] = []

    def reset(self):
        self.session_metrics.clear()

    def track_request(self, provider: str, model: str, usage: Dict[str, int], latency_ms: int):
        metric = {
            "provider": provider,
            "model": model,
            "prompt_tokens": usage.get("prompt_tokens", 0),
            "completion_tokens": usage.get("completion_tokens", 0),
            "total_tokens": usage.get("total_tokens", 0),
            "latency_ms": latency_ms,
            "cost_estimate": round(self._calculate_cost(provider, model, usage), 6),
        }
        self.session_metrics.append(metric)
        logger.log_event("LLM_METRIC", metric)

    def _calculate_cost(self, provider: str, model: str, usage: Dict[str, int]) -> float:
        """
        Đây là bảng giá estimate cho lab demo.
        Bạn có thể sửa lại nếu team muốn dùng giá thật mới nhất.
        """
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)

        pricing = {
            ("openai", "gpt-4o"): {"prompt_per_1k": 0.005, "completion_per_1k": 0.015},
            ("openai", "gpt-4o-mini"): {"prompt_per_1k": 0.00015, "completion_per_1k": 0.0006},
            ("google", "gemini-1.5-flash"): {"prompt_per_1k": 0.000075, "completion_per_1k": 0.0003},
            ("google", "gemini-2.0-flash"): {"prompt_per_1k": 0.0001, "completion_per_1k": 0.0004},
            ("local", "default"): {"prompt_per_1k": 0.0, "completion_per_1k": 0.0},
        }

        key = (provider, model)
        if key not in pricing:
            key = (provider, "default")
        if key not in pricing:
            return 0.0

        rate = pricing[key]
        return (
            (prompt_tokens / 1000.0) * rate["prompt_per_1k"]
            + (completion_tokens / 1000.0) * rate["completion_per_1k"]
        )

    def summary(self) -> Dict[str, Any]:
        if not self.session_metrics:
            return {
                "requests": 0,
                "total_tokens": 0,
                "avg_latency_ms": 0,
                "total_cost_estimate": 0.0,
            }

        total_requests = len(self.session_metrics)
        total_tokens = sum(item["total_tokens"] for item in self.session_metrics)
        avg_latency = sum(item["latency_ms"] for item in self.session_metrics) / total_requests
        total_cost = sum(item["cost_estimate"] for item in self.session_metrics)

        return {
            "requests": total_requests,
            "total_tokens": total_tokens,
            "avg_latency_ms": round(avg_latency, 2),
            "total_cost_estimate": round(total_cost, 6),
        }


tracker = PerformanceTracker()