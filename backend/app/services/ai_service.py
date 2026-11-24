"""
AI service abstraction.

This module is the ONLY place in the codebase that knows how to talk to a
specific vision-language model provider. Routes and other services depend on
the `AIService` interface, never on a concrete provider, so swapping
OpenAI <-> Gemini <-> Qwen-VL <-> a self-hosted LLaVA server is a one-line
config change (AI_PROVIDER in .env) and requires no changes elsewhere.
"""
from __future__ import annotations

import abc
import json
import re
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import Settings


class AIServiceError(Exception):
    """Raised when the AI provider fails or returns something unusable."""


def _extract_json(text: str) -> dict[str, Any]:
    """Best-effort extraction of a JSON object from a model response.

    Models occasionally wrap JSON in markdown fences or add stray text
    despite instructions. This strips fences and grabs the outermost
    {...} block before parsing, then raises AIServiceError on failure so
    callers can apply retry/fallback logic.
    """
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise AIServiceError(f"Model returned invalid JSON: {exc}") from exc

    raise AIServiceError("Model response did not contain a JSON object.")


class BaseVisionProvider(abc.ABC):
    """Common interface every provider adapter must implement."""

    def __init__(self, settings: Settings):
        self.settings = settings

    @abc.abstractmethod
    async def analyze_image(self, image_b64: str, system_prompt: str, user_prompt: str) -> str:
        """Return the raw text response from the model for a vision+text prompt."""

    @abc.abstractmethod
    async def chat_text(self, system_prompt: str, user_prompt: str) -> str:
        """Return the raw text response for a text-only follow-up prompt."""


class OpenAIProvider(BaseVisionProvider):
    """Works with any OpenAI-compatible vision endpoint (OpenAI, Azure OpenAI, etc.)."""

    def _base_url(self) -> str:
        return self.settings.ai_base_url or "https://api.openai.com/v1"

    async def _chat(self, messages: list[dict]) -> str:
        url = f"{self._base_url()}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.settings.ai_api_key}",
            "Content-Type": "application/json",
        }
        payload = {"model": self.settings.ai_model, "messages": messages, "temperature": 0.2}
        async with httpx.AsyncClient(timeout=self.settings.ai_timeout) as client:
            resp = await client.post(url, headers=headers, json=payload)
        if resp.status_code >= 400:
            raise AIServiceError(f"OpenAI API error {resp.status_code}: {resp.text[:500]}")
        data = resp.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise AIServiceError(f"Unexpected OpenAI response shape: {data}") from exc

    async def analyze_image(self, image_b64: str, system_prompt: str, user_prompt: str) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
                ],
            },
        ]
        return await self._chat(messages)

    async def chat_text(self, system_prompt: str, user_prompt: str) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        return await self._chat(messages)


class GeminiProvider(BaseVisionProvider):
    """Google Gemini vision-capable models via the generativelanguage REST API."""

    def _base_url(self) -> str:
        return self.settings.ai_base_url or "https://generativelanguage.googleapis.com/v1beta"

    async def _generate(self, parts: list[dict]) -> str:
        url = (
            f"{self._base_url()}/models/{self.settings.ai_model}:generateContent"
            f"?key={self.settings.ai_api_key}"
        )
        payload = {"contents": [{"parts": parts}]}
        async with httpx.AsyncClient(timeout=self.settings.ai_timeout) as client:
            resp = await client.post(url, json=payload)
        if resp.status_code >= 400:
            raise AIServiceError(f"Gemini API error {resp.status_code}: {resp.text[:500]}")
        data = resp.json()
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as exc:
            raise AIServiceError(f"Unexpected Gemini response shape: {data}") from exc

    async def analyze_image(self, image_b64: str, system_prompt: str, user_prompt: str) -> str:
        parts = [
            {"text": f"{system_prompt}\n\n{user_prompt}"},
            {"inline_data": {"mime_type": "image/jpeg", "data": image_b64}},
        ]
        return await self._generate(parts)

    async def chat_text(self, system_prompt: str, user_prompt: str) -> str:
        parts = [{"text": f"{system_prompt}\n\n{user_prompt}"}]
        return await self._generate(parts)


class OpenAICompatibleLocalProvider(BaseVisionProvider):
    """Covers Qwen-VL / LLaVA servers exposed behind an OpenAI-compatible API
    (e.g. vLLM, Ollama with an OpenAI shim, text-generation-webui, LM Studio)."""

    def _base_url(self) -> str:
        return self.settings.ai_base_url or "http://localhost:8000/v1"

    async def _chat(self, messages: list[dict]) -> str:
        url = f"{self._base_url()}/chat/completions"
        headers = {"Content-Type": "application/json"}
        if self.settings.ai_api_key:
            headers["Authorization"] = f"Bearer {self.settings.ai_api_key}"
        payload = {"model": self.settings.ai_model, "messages": messages, "temperature": 0.2}
        async with httpx.AsyncClient(timeout=self.settings.ai_timeout) as client:
            resp = await client.post(url, headers=headers, json=payload)
        if resp.status_code >= 400:
            raise AIServiceError(f"{self.settings.ai_provider} API error {resp.status_code}: {resp.text[:500]}")
        data = resp.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise AIServiceError(f"Unexpected response shape: {data}") from exc

    async def analyze_image(self, image_b64: str, system_prompt: str, user_prompt: str) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
                ],
            },
        ]
        return await self._chat(messages)

    async def chat_text(self, system_prompt: str, user_prompt: str) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        return await self._chat(messages)


_PROVIDER_REGISTRY: dict[str, type[BaseVisionProvider]] = {
    "openai": OpenAIProvider,
    "gemini": GeminiProvider,
    "qwen": OpenAICompatibleLocalProvider,
    "llava": OpenAICompatibleLocalProvider,
}


def get_provider(settings: Settings) -> BaseVisionProvider:
    provider_cls = _PROVIDER_REGISTRY.get(settings.ai_provider.lower())
    if provider_cls is None:
        raise AIServiceError(
            f"Unknown AI_PROVIDER '{settings.ai_provider}'. "
            f"Valid options: {list(_PROVIDER_REGISTRY.keys())}"
        )
    return provider_cls(settings)


class AIService:
    """High-level facade used by routes. Wraps the provider with retries and
    safe JSON parsing/fallback so callers always get a dict back or a clear
    AIServiceError."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.provider = get_provider(settings)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
    async def _analyze_with_retry(self, image_b64: str, system_prompt: str, user_prompt: str) -> str:
        return await self.provider.analyze_image(image_b64, system_prompt, user_prompt)

    async def analyze_image_structured(self, image_b64: str, system_prompt: str, user_prompt: str) -> dict:
        try:
            raw = await self._analyze_with_retry(image_b64, system_prompt, user_prompt)
        except Exception as exc:  # noqa: BLE001
            raise AIServiceError(f"AI provider request failed after retries: {exc}") from exc

        try:
            return _extract_json(raw)
        except AIServiceError:
            # One repair attempt: ask the model to fix its own output.
            repair_prompt = (
                "Your previous response was not valid JSON. Re-send ONLY the corrected "
                f"JSON object, nothing else. Previous response:\n{raw[:4000]}"
            )
            try:
                repaired = await self.provider.chat_text(system_prompt, repair_prompt)
                return _extract_json(repaired)
            except Exception as exc:  # noqa: BLE001
                raise AIServiceError(f"AI response could not be parsed as JSON: {exc}") from exc

    async def chat_text(self, system_prompt: str, user_prompt: str) -> str:
        try:
            return await self.provider.chat_text(system_prompt, user_prompt)
        except Exception as exc:  # noqa: BLE001
            raise AIServiceError(f"AI provider request failed: {exc}") from exc
