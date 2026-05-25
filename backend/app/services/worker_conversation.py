from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class WorkerCommandResult:
    action: str
    reply: str
    data: dict


class WorkerConversationService:
    def handle_message(self, store, worker_id: str, message: str) -> WorkerCommandResult:
        normalized = message.strip().lower()
        if normalized.startswith("unavailable"):
            return self._set_unavailable(store, worker_id, message)
        if normalized in {"accept", "yes"}:
            return WorkerCommandResult("accept", "Accepted. We will update the customer.", {})
        if normalized in {"decline", "no"}:
            return WorkerCommandResult("decline", "Declined. We will offer this to another worker.", {})
        if normalized in {"arrived", "start", "started", "completed"}:
            return WorkerCommandResult(normalized, f"Marked {normalized}.", {})
        return WorkerCommandResult("unknown", "Reply accept, decline, arrived, started, completed, or unavailable with a date.", {})

    def earnings_breakdown(self, task: dict, payout: dict, upi_hint: str = "xxxxxxxx") -> str:
        gross = float(payout.get("gross_amount", task.get("price", 0.0)))
        fee = float(payout.get("platform_fee", 0.0))
        net = float(payout.get("net_amount", payout.get("amount", 0.0)))
        return "\n".join(
            [
                f"Task: {task.get('title', 'Service request')}",
                f"Earnings: Rs {gross:.2f}",
                f"Platform fee: Rs {fee:.2f}",
                f"Your payout: Rs {net:.2f}",
                f"Paid to UPI: {upi_hint}",
            ]
        )

    def _set_unavailable(self, store, worker_id: str, message: str) -> WorkerCommandResult:
        worker = store.workers.get(worker_id)
        if not worker:
            return WorkerCommandResult("not_found", "Worker profile was not found.", {})
        unavailable_date = self._extract_date(message)
        worker.setdefault("unavailable_dates", []).append(unavailable_date.isoformat())
        return WorkerCommandResult(
            "unavailable",
            f"You are marked unavailable on {unavailable_date.isoformat()}.",
            {"date": unavailable_date.isoformat()},
        )

    def _extract_date(self, message: str) -> date:
        for token in message.replace(",", " ").split():
            try:
                return datetime.fromisoformat(token).date()
            except ValueError:
                continue
        # Product assumption: vague unavailable requests mean today, which is safer than ignoring the worker.
        return date.today()
