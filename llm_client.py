# llm_client.py
"""
LLM client abstraction with:
- Support for multiple backends:
    - Ollama (default, local & free)
    - OpenAI cloud (optional)
    - Local echo (for offline/testing)
- Simple task-based model routing via `task_type`.

Usage example:

    from llm_client import LLMClient
    client = LLMClient()  # uses env LLM_PROVIDER (default: 'ollama')

    # General email summary
    text = client.generate(prompt, task_type="email")

    # Resume tailoring
    text = client.generate(prompt, task_type="resume")

    # Coding / Playwright script
    text = client.generate(prompt, task_type="code")
"""
from __future__ import annotations

import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

# --- Environment defaults ---

# 'ollama' (local, default), 'openai' (cloud), or 'local' (echo only)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()

# For Ollama we use the OpenAI-compatible endpoint by default
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "http://localhost:11434/v1").rstrip("/")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "ollama")

# Default model (used if no task-specific override)
DEFAULT_MODEL = (
    os.getenv("MODEL_DEFAULT")
    or os.getenv("OPENAI_MODEL")
    or "llama3.1:8b"
)

# Task → model routing (can be overridden via env)
TASK_MODEL_MAP = {
    "default": DEFAULT_MODEL,  # general writing / summaries
    "email": os.getenv("MODEL_EMAIL", DEFAULT_MODEL),
    "resume": os.getenv("MODEL_RESUME", DEFAULT_MODEL),
    "long_context": os.getenv("MODEL_LONG", "qwen2.5:14b"),
    "code": os.getenv("MODEL_CODE", "deepseek-coder-v2:16b"),
    "repo_agent": os.getenv("MODEL_REPO", "devstral-small-2"),
    "fast": os.getenv("MODEL_FAST", "phi3:3.8b"),
}


class LLMClient:
    def __init__(self, provider: Optional[str] = None):
        """
        provider:
            - 'ollama' (default): local, free, uses HTTP to OpenAI-compatible API.
            - 'openai': real OpenAI cloud (requires OPENAI_API_KEY).
            - 'local': echo-only; no external calls.
        """
        self.provider = (provider or LLM_PROVIDER).lower()

        if self.provider == "openai":
            # Cloud OpenAI using the official SDK
            from openai import OpenAI  # type: ignore

            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise RuntimeError(
                    "OPENAI_API_KEY is not set. Add it to your environment or .env file."
                )

            base_url = os.getenv("OPENAI_API_BASE") or None
            self._client = OpenAI(api_key=api_key, base_url=base_url)
            self._mode = "openai_sdk"

        elif self.provider == "ollama":
            # Local Ollama via raw HTTP (OpenAI-compatible /chat/completions)
            import requests  # type: ignore

            self._client = requests
            self._mode = "ollama_http"
            self._base_url = OPENAI_API_BASE
            self._api_key = OPENAI_API_KEY

        else:
            # Local echo only, no HTTP calls
            self._client = None
            self._mode = "local_echo"

    # --- Routing helpers ---

    def _choose_model(self, task_type: Optional[str]) -> str:
        """Return model name based on task_type and env configuration."""
        if not task_type:
            return TASK_MODEL_MAP["default"]
        return TASK_MODEL_MAP.get(task_type, TASK_MODEL_MAP["default"])

    # --- Main API ---

    def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.2,
        task_type: Optional[str] = None,
    ) -> str:
        """
        Generate a completion for the given prompt.

        task_type can be one of:
            'email', 'resume', 'long_context', 'code', 'repo_agent', 'fast', or None.

        The chosen model can be configured via environment variables.
        """
        model = self._choose_model(task_type)

        if self._mode == "openai_sdk":
            # Uses the official OpenAI Python client (cloud or compatible base_url)
            resp = self._client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
            )
            choice = resp.choices[0]
            msg = getattr(choice, "message", None)
            if msg is not None:
                # SDK v1 style (object) or dict-like
                if isinstance(msg, dict):
                    return (msg.get("content") or "").strip()
                return getattr(msg, "content", "").strip()

            # Fallback for unexpected shapes
            if hasattr(choice, "text"):
                return choice.text.strip()
            return str(choice)

        if self._mode == "ollama_http":
            # Basic HTTP call to an OpenAI-compatible /chat/completions endpoint
            url = f"{self._base_url}/chat/completions"
            headers = {
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
            }

            r = self._client.post(url, headers=headers, json=payload, timeout=120)
            r.raise_for_status()
            data = r.json()
            try:
                return data["choices"][0]["message"]["content"].strip()
            except Exception:
                # Fallback: just dump the JSON if shape is odd
                return str(data)

        # Local echo fallback (no external calls)
        truncated = prompt[:1200]
        return f"[LOCAL_ECHO provider={self.provider} model={model}]\n{truncated}"

    def __repr__(self) -> str:
        return f"<LLMClient provider={self.provider!r} mode={self._mode!r}>"



if __name__ == "__main__":
    client = LLMClient()
    print(client)
    out = client.generate("Say hello in one short sentence.", task_type="default", max_tokens=32)
    print("LLM output:\n", out)
