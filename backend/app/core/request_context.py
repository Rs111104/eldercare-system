from __future__ import annotations

from contextvars import ContextVar
from typing import Any


request_id_var: ContextVar[str] = ContextVar("request_id", default="")
user_id_var: ContextVar[str] = ContextVar("user_id", default="")
role_var: ContextVar[str] = ContextVar("role", default="")
action_var: ContextVar[str] = ContextVar("action", default="")


def current_log_context() -> dict[str, Any]:
    return {
        "request_id": request_id_var.get(),
        "user_id": user_id_var.get(),
        "role": role_var.get(),
        "action": action_var.get(),
    }
