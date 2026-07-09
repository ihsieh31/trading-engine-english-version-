from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass
from typing import Any

from openai import OpenAI

from config import Config

log = logging.getLogger(__name__)


@dataclass
class LLMResponse:
    text: str
    model: str
    usage: dict | None = None


class LLMClient:
    """Unified LLM client with retry, timeout, thinking support, and multi-strategy JSON parsing.

    Ported from daily_stock_analysis's LLMToolAdapter + runner.py patterns:
    - call_text / call_json unified interface
    - Exponential backoff on transient errors
    - Multi-strategy JSON recovery (fenced blocks → raw parse → brace substring)
    - Thinking mode support for reasoning models
    - Configurable model, temperature, and timeout per call
    """

    def __init__(self, config: Config | None = None):
        self._cfg = config or Config()
        self._client: OpenAI | None = None

    def _get_client(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI(
                api_key=self._cfg.OPENAI_COMPATIBLE_API_KEY,
                base_url=self._cfg.LLM_BACKEND_URL,
            )
        return self._client

    def call_text(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.3,
        max_retries: int = 2,
        timeout_sec: float = 60.0,
        enable_thinking: bool = False,
    ) -> LLMResponse:
        model = model or self._cfg.DEEP_THINK_MODEL
        client = self._get_client()
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "timeout": timeout_sec,
        }
        if enable_thinking:
            extra = self._get_thinking_extra_body(model)
            if extra:
                kwargs["extra_body"] = extra

        last_error: Exception | None = None
        for attempt in range(1 + max_retries):
            try:
                resp = client.chat.completions.create(**kwargs)
                text = resp.choices[0].message.content or ""
                usage = None
                if resp.usage:
                    usage = {
                        "prompt_tokens": resp.usage.prompt_tokens,
                        "completion_tokens": resp.usage.completion_tokens,
                        "total_tokens": resp.usage.total_tokens,
                    }
                return LLMResponse(text=text, model=model, usage=usage)
            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    delay = 1.5 ** attempt
                    log.warning(f"LLM call attempt {attempt + 1} failed: {e}. Retrying in {delay:.1f}s...")
                    time.sleep(delay)
        raise RuntimeError(f"LLM call failed after {max_retries + 1} attempts") from last_error

    def call_json(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.3,
        max_retries: int = 2,
        timeout_sec: float = 60.0,
        enable_thinking: bool = False,
    ) -> tuple[dict[str, Any] | None, LLMResponse]:
        """Call LLM and attempt multi-strategy JSON parsing on the response.

        Returns (parsed_dict, raw_response). Returns (None, raw_response) if parsing fails.
        """
        raw = self.call_text(
            messages=messages,
            model=model,
            temperature=temperature,
            max_retries=max_retries,
            timeout_sec=timeout_sec,
            enable_thinking=enable_thinking,
        )
        parsed = self._try_parse_json(raw.text)
        return parsed, raw

    @staticmethod
    def _get_thinking_extra_body(model: str) -> dict | None:
        """Generate thinking activation payload for supported models.

        Ported from daily_stock_analysis llm_adapter.py get_thinking_extra_body().
        """
        model_lower = model.lower()
        if "agnes" in model_lower:
            return {"chat_template_kwargs": {"enable_thinking": True}}
        return None

    @staticmethod
    def _try_parse_json(text: str) -> dict[str, Any] | None:
        """Multi-strategy JSON extraction from LLM output.

        Ported from daily_stock_analysis runner.py try_parse_json().
        Strategies in order:
        1. Direct json.loads on cleaned text
        2. Markdown code fences (```json ... ```)
        3. Brace-delimited substring
        """
        if not text:
            return None

        candidates: list[str] = []
        cleaned = text.strip()
        if cleaned:
            candidates.append(cleaned)

        # Markdown code fences
        if cleaned.startswith("```"):
            unfenced = re.sub(r"^```(?:json)?\s*", "", cleaned)
            unfenced = re.sub(r"\s*```$", "", unfenced)
            if unfenced:
                candidates.append(unfenced.strip())

        fenced_blocks = re.findall(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
        for block in fenced_blocks:
            block = block.strip()
            if block:
                candidates.append(block)

        # Brace-delimited substring
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            snippet = text[start:end + 1].strip()
            if snippet:
                candidates.append(snippet)

        seen: set[str] = set()
        for candidate in candidates:
            if candidate in seen:
                continue
            seen.add(candidate)
            try:
                obj = json.loads(candidate)
                if isinstance(obj, dict):
                    return obj
            except json.JSONDecodeError:
                continue

        log.warning(f"Failed to parse JSON from LLM response (tried {len(candidates)} candidate(s))")
        return None
