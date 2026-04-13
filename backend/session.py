from __future__ import annotations

from dataclasses import asdict, dataclass, field
from threading import Lock
from typing import Any

from .models import ProblemSnapshot, SolveDraft


@dataclass
class SessionState:
    running: bool = False
    stopped: bool = False
    auto_solve: bool = False
    auto_advance: bool = False
    current_problem: dict[str, Any] = field(default_factory=dict)
    last_result: dict[str, Any] = field(default_factory=dict)
    history: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SessionManager:
    def __init__(self) -> None:
        self._state = SessionState()
        self._lock = Lock()

    def get_state(self) -> dict[str, Any]:
        with self._lock:
            return self._state.to_dict()

    def stop(self) -> dict[str, Any]:
        with self._lock:
            self._state.running = False
            self._state.stopped = True
            return self._state.to_dict()

    def update_settings(self, auto_solve: bool | None, auto_advance: bool | None) -> dict[str, Any]:
        with self._lock:
            if auto_solve is not None:
                self._state.auto_solve = auto_solve
            if auto_advance is not None:
                self._state.auto_advance = auto_advance
            return self._state.to_dict()

    def begin(self, problem: ProblemSnapshot, auto_solve: bool, auto_advance: bool) -> dict[str, Any]:
        with self._lock:
            self._state.running = True
            self._state.stopped = False
            self._state.auto_solve = auto_solve
            self._state.auto_advance = auto_advance
            self._state.current_problem = problem.to_dict()
            return self._state.to_dict()

    def complete(self, problem: ProblemSnapshot, draft: SolveDraft) -> dict[str, Any]:
        entry = {
            "problem": problem.to_dict(),
            "result": draft.to_dict(),
        }
        with self._lock:
            self._state.running = False
            self._state.current_problem = problem.to_dict()
            self._state.last_result = draft.to_dict()
            self._state.history.append(entry)
            self._state.history = self._state.history[-20:]
            return self._state.to_dict()
