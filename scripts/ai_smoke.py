"""Manual smoke test of the AI consultant against a real OpenAI-compatible LLM (no DB, no Telegram).

    GEMINI_API_KEY=... [LLM_MODEL=gemini-3.5-flash-lite] python scripts/ai_smoke.py "Потрібно 4 камери на будинок"

Uses the real catalog; supplier stock is stubbed. Never prints the key.
"""
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ.setdefault("DATABASE_URL", "postgresql://smoke:smoke@127.0.0.1:1/smoke")
os.environ.setdefault("BOT_TOKEN", "")

from bot.ai.consultant import Consultant  # noqa: E402
from bot.ai.llm import LLMClient  # noqa: E402
from bot.config import get_settings  # noqa: E402


async def stub_stock(items):
    return [{"id": i["id"], "stock": "перевірити вручну"} for i in items]


async def main(prompts):
    settings = get_settings()
    if not settings.llm_api_key:
        raise SystemExit("GEMINI_API_KEY is not set")
    consultant = Consultant(LLMClient.from_settings(settings), stock_checker=stub_stock)
    print(f"model={settings.llm_model} base={settings.llm_base_url}")
    history = []
    for prompt in prompts:
        history.append({"role": "user", "content": prompt})
        result = await consultant.reply(history)
        print(f"\n>>> {prompt}\n<<< handoff={result.handoff} tools={result.tools_used}\n{result.text}")
        if result.text:
            history.append({"role": "assistant", "content": result.text})


asyncio.run(main(sys.argv[1:] or ["Вітаю! Потрібно 4 камери на приватний будинок, вулиця."]))
