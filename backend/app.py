from __future__ import annotations

from typing import Any

from .models import ProblemSnapshot
from .providers import BaseProvider, create_provider, create_provider_from_settings, default_provider_settings
from .session import SessionManager


class LeetCodeCopilotApp:
    def __init__(self, provider: BaseProvider | None = None, sessions: SessionManager | None = None) -> None:
        self.provider_settings = default_provider_settings()
        self.provider = provider or create_provider()
        self.sessions = sessions or SessionManager()

    def health(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "provider": self.provider.name,
            "model": self.provider_settings.get("model", ""),
        }

    def state(self) -> dict[str, Any]:
        return self.sessions.get_state()

    def stop(self) -> dict[str, Any]:
        return self.sessions.stop()

    def update_settings(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.sessions.update_settings(
            auto_solve=payload.get("autoSolve"),
            auto_advance=payload.get("autoAdvance"),
        )

    def configure_provider(self, payload: dict[str, Any]) -> dict[str, Any]:
        settings = default_provider_settings()

        provider = str(payload.get("provider", "")).strip().lower()
        if provider:
            settings["provider"] = provider

        api_key = str(payload.get("apiKey", "")).strip()
        if api_key:
            settings["apiKey"] = api_key

        model = str(payload.get("model", "")).strip()
        if model:
            settings["model"] = model

        api_url = str(payload.get("apiUrl", "")).strip()
        if api_url:
            settings["apiUrl"] = api_url

        self.provider_settings = settings
        self.provider = create_provider_from_settings(settings)
        return {
            "status": "configured",
            "provider": self.provider.name,
            "model": settings["model"],
            "hasApiKey": bool(settings["apiKey"]),
        }

    def solve(self, payload: dict[str, Any]) -> dict[str, Any]:
        problem = ProblemSnapshot.from_payload(payload.get("problem", payload))
        auto_solve = bool(payload.get("autoSolve", False))
        auto_advance = bool(payload.get("autoAdvance", False))
        self.sessions.begin(problem, auto_solve=auto_solve, auto_advance=auto_advance)
        draft = self.provider.generate(problem)
        state = self.sessions.complete(problem, draft)
        return {
            "status": "draft_ready",
            "problem": problem.to_dict(),
            "draft": draft.to_dict(),
            "state": state,
        }
