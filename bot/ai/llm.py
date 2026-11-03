"""Minimal OpenAI-compatible chat-completions client (works with Gemini's /v1beta/openai/ endpoint).

Free tiers are rate limited: requests are spaced by AI_MIN_INTERVAL_SECONDS, 429/5xx are retried with a short
backoff (Retry-After respected, total wait capped), and a daily request budget protects the quota. Any failure
raises LLMUnavailable so the caller can hand the conversation to the owner instead of going silent.
"""
from __future__ import annotations

import asyncio
import logging
import time
from datetime import date
from typing import Any

from aiohttp import ClientError, ClientSession, ClientTimeout

logger = logging.getLogger("altcam.ai.llm")
RETRY_STATUSES = {429, 500, 502, 503, 504}


class LLMUnavailable(Exception):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


class LLMClient:
    _lock = asyncio.Lock()
    _last_call = 0.0
    _day: date | None = None
    _count = 0

    def __init__(self, api_key: str, base_url: str, model: str, *, timeout: float = 30, min_interval: float = 4,
                 daily_limit: int = 200, max_retries: int = 2, max_wait: float = 12, session_factory=ClientSession):
        self.api_key, self.base_url, self.model = api_key, base_url.rstrip("/"), model
        self.timeout, self.min_interval, self.daily_limit = timeout, min_interval, daily_limit
        self.max_retries, self.max_wait, self.session_factory = max_retries, max_wait, session_factory

    @classmethod
    def from_settings(cls, settings) -> "LLMClient":
        return cls(settings.llm_api_key, settings.llm_base_url, settings.llm_model, timeout=settings.ai_timeout_seconds,
                   min_interval=settings.ai_min_interval_seconds, daily_limit=settings.ai_daily_request_limit)

    async def _throttle(self) -> None:
        cls = type(self)
        async with cls._lock:
            today = date.today()
            if cls._day != today:
                cls._day, cls._count = today, 0
            if self.daily_limit and cls._count >= self.daily_limit:
                raise LLMUnavailable("daily_limit")
            wait = cls._last_call + self.min_interval - time.monotonic()
            if wait > 0:
                await asyncio.sleep(wait)
            cls._last_call = time.monotonic()
            cls._count += 1

    async def chat(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None) -> dict[str, Any]:
        body: dict[str, Any] = {"model": self.model, "messages": messages, "temperature": 0.3}
        if tools:
            body["tools"], body["tool_choice"] = tools, "auto"
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        waited = 0.0
        for attempt in range(self.max_retries + 1):
            await self._throttle()
            try:
                async with self.session_factory(timeout=ClientTimeout(total=self.timeout)) as client:
                    async with client.post(f"{self.base_url}/chat/completions", json=body, headers=headers) as response:
                        status = response.status
                        retry_after = response.headers.get("Retry-After")
                        payload = await response.json(content_type=None) if status == 200 else await response.text()
            except (ClientError, asyncio.TimeoutError) as exc:
                logger.warning("llm_transport_error attempt=%s (%s)", attempt, type(exc).__name__)
                status, retry_after, payload = 503, None, ""
            if status == 200:
                try:
                    return payload["choices"][0]["message"]
                except (KeyError, IndexError, TypeError) as exc:
                    raise LLMUnavailable("bad_response") from exc
            if status not in RETRY_STATUSES:
                logger.warning("llm_error status=%s body=%s", status, str(payload)[:300])
                raise LLMUnavailable(f"http_{status}")
            delay = float(retry_after) if (retry_after or "").replace(".", "", 1).isdigit() else 2.0 * (2 ** attempt)
            if attempt == self.max_retries or waited + delay > self.max_wait:
                logger.warning("llm_giving_up status=%s attempts=%s", status, attempt + 1)
                raise LLMUnavailable("rate_limited" if status == 429 else f"http_{status}")
            waited += delay
            await asyncio.sleep(delay)
        raise LLMUnavailable("exhausted")
