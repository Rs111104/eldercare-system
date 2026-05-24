from __future__ import annotations

from app.store import store


class PayoutService:
    async def process_task_payout(self, task_id: str, worker_id: str, amount: float) -> dict:
        return {"payouts": store.record_payout_split(worker_id, task_id, amount)}

    async def get_pending_payouts(self, worker_id: str):
        return store.get_payouts_for_worker(worker_id)

    async def get_worker_total_earnings(self, worker_id: str) -> dict:
        return store.get_earnings_for_worker(worker_id)

    async def release_immediate_payout(self, payout_id: str) -> bool:
        payout = store.payouts.get(payout_id)
        if not payout:
            return False
        payout["status"] = "released"
        return True

    async def release_verification_payout(self, payout_id: str) -> bool:
        return await self.release_immediate_payout(payout_id)

    async def get_payout_history(self, worker_id: str, limit: int = 20, offset: int = 0):
        return store.get_payouts_for_worker(worker_id)[offset : offset + limit]

    async def get_payout_status(self, payout_id: str) -> dict:
        return store.payouts.get(payout_id, {})
