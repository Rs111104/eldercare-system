from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class TaskStore(Protocol):
    def transition_task(self, task_id: str, next_state: str, actor_id: str, role: str, reason: str = "") -> dict:
        ...


@dataclass(frozen=True)
class TaskLifecycleService:
    store: TaskStore

    def transition(self, task_id: str, next_state: str, actor_id: str, role: str, reason: str) -> dict:
        if not reason.strip():
            raise ValueError("Task transitions require a reason")
        return self.store.transition_task(
            task_id=task_id,
            next_state=next_state,
            actor_id=actor_id,
            role=role,
            reason=reason,
        )
