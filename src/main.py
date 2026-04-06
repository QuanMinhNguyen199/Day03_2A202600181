import argparse
import os
import sys
import warnings

# Fix Unicode encoding for Vietnamese on Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Add the project root to sys.path to fix ModuleNotFoundError
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Suppress FutureWarning from deprecated google.generativeai
warnings.filterwarnings("ignore", category=FutureWarning, module="google")

from dotenv import load_dotenv

from src.agent.agent import ReActAgent
from src.agent.chatbot import BaselineChatbot
from src.core.gemini_provider import GeminiProvider
from src.core.local_provider import LocalProvider
from src.core.openai_provider import OpenAIProvider
from src.telemetry.logger import logger
from src.telemetry.metrics import tracker
from src.tools.movie_booking_tools import get_tools


def select_provider_interactive():
    """Let the user choose provider at startup."""
    print("\n=== Chọn LLM Provider ===")
    print("  1) Google Gemini (gemini-2.0-flash) — nhanh, qua API")
    print("  2) Local Phi-3 (CPU)                — chậm, offline")
    print("  3) OpenAI / GitHub Models (gpt-4o)  — qua Azure OpenAI")

    while True:
        choice = input("\nNhập 1, 2 hoặc 3 (mặc định=3): ").strip()
        if choice == "1":
            return "google", "gemini-2.0-flash"
        if choice == "2":
            return "local", "Phi-3-mini-4k-instruct"
        if choice in {"", "3"}:
            return "openai", "gpt-4o"
        print("Lựa chọn không hợp lệ. Hãy nhập 1, 2 hoặc 3.")


def build_llm(provider: str = None, model_name: str = None):
    if provider is None:
        provider = os.getenv("DEFAULT_PROVIDER", "local").strip().lower()

    provider_defaults = {
        "openai": "gpt-4o",
        "google": "gemini-2.0-flash",
        "gemini": "gemini-2.0-flash",
        "local": "Phi-3-mini-4k-instruct",
    }

    if model_name is None:
        model_name = os.getenv(
            "DEFAULT_MODEL", provider_defaults.get(provider, "Phi-3-mini-4k-instruct")
        ).strip()

    if provider == "openai":
        return OpenAIProvider(model_name=model_name, api_key=os.getenv("OPENAI_API_KEY"))

    if provider in {"google", "gemini"}:
        return GeminiProvider(model_name=model_name, api_key=os.getenv("GEMINI_API_KEY"))

    model_path = os.getenv("LOCAL_MODEL_PATH", "./models/Phi-3-mini-4k-instruct-q4.gguf")
    return LocalProvider(model_path=model_path, n_ctx=4096)


def interactive_loop(mode: str, llm):
    if mode == "chatbot":
        runner = BaselineChatbot(llm)
        print("=== Chatbot Baseline ===")
    else:
        runner = ReActAgent(llm=llm, tools=get_tools(), max_steps=6)
        print("=== ReAct Movie Booking Agent ===")

    print("Gõ 'exit' để thoát.\n")

    while True:
        user_input = input("Bạn: ").strip()
        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit"}:
            break

        if mode == "chatbot":
            answer = runner.chat(user_input)
        else:
            answer = runner.run(user_input)

        print(f"\nTrợ lý: {answer}\n")

    logger.log_event("SESSION_SUMMARY", tracker.summary())
    tracker.reset()


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Lab 3: Chatbot vs ReAct Agent")
    parser.add_argument("--mode", choices=["chatbot", "agent"], default="agent",
                        help="Chế độ chạy: chatbot (baseline) hoặc agent (ReAct)")
    parser.add_argument("--provider", choices=["google", "local", "openai", "select"],
                        default=None,
                        help="Chọn LLM provider. Dùng 'select' để chọn tương tác.")
    parser.add_argument("--message", type=str, default=None,
                        help="Gửi một tin nhắn và thoát (không vào interactive mode)")
    args = parser.parse_args()

    # Determine provider
    provider_choice = args.provider
    model_choice = None

    if provider_choice == "select":
        provider_choice, model_choice = select_provider_interactive()
    elif provider_choice is None:
        # Use env default, but if in interactive mode (no --message), offer selection
        if args.message is None:
            provider_choice, model_choice = select_provider_interactive()
        else:
            provider_choice = os.getenv("DEFAULT_PROVIDER", "google").strip().lower()

    llm = build_llm(provider=provider_choice, model_name=model_choice)
    logger.info(f"Loaded provider: {provider_choice} | model: {llm.model_name}")

    if args.message:
        if args.mode == "chatbot":
            runner = BaselineChatbot(llm)
            answer = runner.chat(args.message)
        else:
            runner = ReActAgent(llm=llm, tools=get_tools(), max_steps=6)
            answer = runner.run(args.message)

        print(answer)
        logger.log_event("SESSION_SUMMARY", tracker.summary())
        tracker.reset()
        return

    interactive_loop(args.mode, llm)


if __name__ == "__main__":
    main()