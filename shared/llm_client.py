# llm_client.py
#
# Purpose: OpenAI-compatible client for local and remote LLM backends
#
# This module:
# - Lists available models from Ollama or OpenAI-compatible endpoints
# - Sends blocking and streaming chat completion requests
# - Normalizes response shapes across providers

import json
import os
from typing import AsyncIterator

import httpx

BASE_URL = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
API_KEY = os.getenv("LLM_API_KEY", "ollama")


class LLMClient:
    def __init__(self, base_url: str = BASE_URL, api_key: str = API_KEY) -> None:
        self.base_url = base_url.rstrip("/")
        self.headers = {"Authorization": f"Bearer {api_key}"}

    async def list_models(self) -> list[str]:
        async with httpx.AsyncClient() as c:
            try:
                r = await c.get(f"{self.base_url}/models", headers=self.headers, timeout=5)
                if r.status_code == 200:
                    return [m["id"] for m in r.json().get("data", [])]
            except Exception:
                pass

            try:
                root = self.base_url.removesuffix("/v1")
                r = await c.get(f"{root}/api/tags", timeout=5)
                if r.status_code == 200:
                    return [m["name"] for m in r.json().get("models", [])]
            except Exception:
                pass

        return []

    async def complete(self, messages: list[dict], model: str) -> str:
        async with httpx.AsyncClient() as c:
            r = await c.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json={"model": model, "messages": messages, "stream": False},
                timeout=30,
            )
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]

    async def stream_complete(
        self, messages: list[dict], model: str
    ) -> AsyncIterator[str]:
        async with httpx.AsyncClient() as c:
            async with c.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json={"model": model, "messages": messages, "stream": True},
                timeout=60,
            ) as r:
                r.raise_for_status()
                async for line in r.aiter_lines():
                    if line.startswith("data: ") and "DONE" not in line:
                        try:
                            chunk = json.loads(line[6:])
                            token = chunk["choices"][0]["delta"].get("content", "")
                            if token:
                                yield token
                        except Exception:
                            pass
