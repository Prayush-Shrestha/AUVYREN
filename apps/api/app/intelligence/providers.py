"""AI provider abstraction: deterministic, local Ollama, cloud interface stub.

All providers implement one server-side interface. Routes never call a provider
directly; they go through IntelligenceService, which minimizes context, chooses
the provider only if allowed and healthy, and falls back to deterministic output.
"""

from __future__ import annotations

import hashlib
import json
import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Protocol, runtime_checkable

import httpx

if TYPE_CHECKING:
    pass


@dataclass(frozen=True)
class AIRequest:
    task: str  # 'summarize', 'review', 'ask', 'plan', 'analyze'
    system_instructions: str
    context: dict  # minimized, user-scoped data
    max_output_tokens: int
    temperature: float = 0.2


@dataclass(frozen=True)
class AIResponse:
    text: str
    provider: str
    model: str | None
    usage: dict | None  # input/output tokens when available
    generated_at: str


@runtime_checkable
class AIProvider(Protocol):
    name: str

    async def health(self) -> dict: ...
    async def list_models(self) -> list[str]: ...
    async def generate(self, request: AIRequest) -> AIResponse: ...


@dataclass(frozen=True)
class ProviderHealth:
    name: str
    healthy: bool
    detail: str
    models: list[str] = field(default_factory=list)


class DeterministicProvider:
    """Always-available provider that returns deterministic summaries."""

    name = "deterministic"

    async def health(self) -> dict:
        return {"name": self.name, "healthy": True, "detail": "Always available"}

    async def list_models(self) -> list[str]:
        return ["deterministic"]

    async def generate(self, request: AIRequest) -> AIResponse:
        context = request.context
        lines = [f"Deterministic summary for: {request.task}"]
        if context.get("tasks"):
            lines.append(f"- {len(context['tasks'])} task(s) in context")
        if context.get("goals"):
            lines.append(f"- {len(context['goals'])} goal(s) in context")
        if context.get("habits"):
            lines.append(f"- {len(context['habits'])} habit(s) in context")
        lines.append(
            "No model was used. This is a rules-based summary of your data."
        )
        return AIResponse(
            text="\n".join(lines),
            provider=self.name,
            model=None,
            usage=None,
            generated_at=datetime.now(UTC).isoformat(),
        )


class OllamaProvider:
    """Local Ollama provider. Self-hosted only; browser cannot reach localhost."""

    name = "ollama"

    def __init__(
        self,
        base_url: str,
        model: str,
        timeout_seconds: int = 120,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    async def health(self) -> dict:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                if resp.status_code == 200:
                    models = [m.get("name", "") for m in resp.json().get("models", [])]
                    return {
                        "name": self.name,
                        "healthy": True,
                        "detail": "Ollama reachable",
                        "models": models,
                    }
                return {
                    "name": self.name,
                    "healthy": False,
                    "detail": f"Ollama returned {resp.status_code}",
                    "models": [],
                }
        except Exception as exc:  # noqa: BLE001 - surface connection failure
            return {
                "name": self.name,
                "healthy": False,
                "detail": f"Ollama unreachable: {exc}",
                "models": [],
            }

    async def list_models(self) -> list[str]:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                if resp.status_code == 200:
                    return [m.get("name", "") for m in resp.json().get("models", [])]
        except Exception:  # noqa: BLE001
            pass
        return []

    async def generate(self, request: AIRequest) -> AIResponse:
        payload = {
            "model": self.model,
            "prompt": (
                f"{request.system_instructions}\n\nContext:\n"
                f"{json.dumps(request.context, indent=2)}\n\nTask: {request.task}"
            ),
            "stream": False,
            "options": {
                "num_predict": request.max_output_tokens,
                "temperature": request.temperature,
            },
        }
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            resp = await client.post(f"{self.base_url}/api/generate", json=payload)
            resp.raise_for_status()
            data = resp.json()
        return AIResponse(
            text=data.get("response", ""),
            provider=self.name,
            model=self.model,
            usage={
                "prompt_eval_count": data.get("prompt_eval_count"),
                "eval_count": data.get("eval_count"),
            },
            generated_at=datetime.now(UTC).isoformat(),
        )


class CloudAIProvider:
    """Cloud AI interface stub (Phase 6). Never used in Phase 4.

    Raising on any call makes the Phase 4 "no cloud transmission" rule
    enforceable at runtime rather than by convention.
    """

    name = "cloud"

    async def health(self) -> dict:
        return {
            "name": self.name,
            "healthy": False,
            "detail": "Cloud AI not available in Phase 4",
        }

    async def list_models(self) -> list[str]:
        return []

    async def generate(self, request: AIRequest) -> AIResponse:
        raise NotImplementedError(
            "Cloud AI is a Phase 6 feature; no cloud calls are made in Phase 4"
        )


def mask_secret(value: str | None) -> str | None:
    """Mask a secret for safe display/logging."""
    if not value:
        return None
    return f"****{value[-4:]}" if len(value) > 4 else "****"


def secret_hash(value: str | None) -> str | None:
    """Stable hash of a secret for change detection (never the secret itself)."""
    if not value:
        return None
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def new_provider_secret() -> str:
    """Generate a provider secret for encrypted storage."""
    return secrets.token_urlsafe(32)
