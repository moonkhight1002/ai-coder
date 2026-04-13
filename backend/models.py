from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class ProblemSnapshot:
    platform: str
    title: str
    slug: str
    url: str
    statement: str
    language: str = "python"
    starter_code: str = ""
    next_url: str = ""
    examples: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "ProblemSnapshot":
        return cls(
            platform=str(payload.get("platform", "")).strip(),
            title=str(payload.get("title", "")).strip(),
            slug=str(payload.get("slug", "")).strip(),
            url=str(payload.get("url", "")).strip(),
            statement=str(payload.get("statement", "")).strip(),
            language=str(payload.get("language", "python")).strip() or "python",
            starter_code=str(payload.get("starterCode", payload.get("starter_code", ""))),
            next_url=str(payload.get("nextUrl", payload.get("next_url", ""))).strip(),
            examples=list(payload.get("examples", [])),
            constraints=list(payload.get("constraints", [])),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SolveDraft:
    provider: str
    code: str
    analysis: str
    complexity: str
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
