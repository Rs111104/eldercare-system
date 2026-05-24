from __future__ import annotations

from app.store import store


class PricingService:
    async def calculate_price(self, service_type: str, distance_km: float, effort_level: int = 1, urgency_level: int = 1, travel_time_minutes: float = 0.0) -> dict:
        config = store.get_pricing_config(service_type) or {"base_price": 100.0}
        urgency = 1.0 + max(0, min(urgency_level, 5) - 1) * 0.125
        total_price = round((float(config.get("base_price", 100.0)) + (distance_km * 5.0)) * urgency, 2)
        return {"base_price": float(config.get("base_price", 100.0)), "distance_km": distance_km, "urgency": round(urgency, 2), "total_price": total_price, "urgency_multiplier": round(urgency, 2)}

    async def get_quick_mode_price(self, service_type: str, distance_km: float, effort_level: int = 2) -> dict:
        return await self.calculate_price(service_type, distance_km, effort_level, urgency_level=4)

    async def get_scheduled_mode_price(self, service_type: str, distance_km: float, effort_level: int = 2) -> dict:
        return await self.calculate_price(service_type, distance_km, effort_level, urgency_level=1)

    async def update_pricing_config(self, service_type: str, base_price: float, distance_charge_per_km: float, effort_multiplier: float = 1.0) -> dict:
        return store.upsert_pricing_config(service_type, base_price, distance_charge_per_km)
