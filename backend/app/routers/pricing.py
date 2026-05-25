from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.models import PricingConfigRequest, PricingRequest
from app.core.deps import require_role
from app.store import store

router = APIRouter()


def _calculate(service_type: str, distance_km: float, urgency: float) -> dict:
    config = store.get_pricing_config(service_type) or store.get_pricing_config("other") or {"base_price": 100.0, "per_km_rate": 5.0}
    base_price = float(config.get("base_price", 100.0))
    total_price = round((base_price + (distance_km * 5.0)) * urgency, 2)
    return {
        "service_type": service_type,
        "base_price": round(base_price, 2),
        "distance_km": round(distance_km, 2),
        "urgency": round(urgency, 2),
        "urgency_multiplier": round(urgency, 2),
        "total_price": total_price,
    }


@router.post("/calculate")
async def calculate_pricing(payload: PricingRequest):
    urgency = payload.urgency
    if payload.urgency_level is not None:
        urgency = 1.0 + max(0, min(payload.urgency_level, 5) - 1) * 0.125
    return store.calculate_pricing_breakdown(
        payload.service_type,
        payload.distance_km,
        urgency,
        customer_id=payload.customer_id,
        same_day_bundle=payload.same_day_bundle,
    )


@router.post("/calculate-with-urgency")
async def calculate_pricing_with_urgency(payload: PricingRequest):
    return await calculate_pricing(payload)


@router.get("/quick-mode/{service_type}")
async def quick_mode_price(service_type: str, distance_km: float = 0.0):
    return store.calculate_pricing_breakdown(service_type, distance_km, 1.25)


@router.get("/scheduled-mode/{service_type}")
async def scheduled_mode_price(service_type: str, distance_km: float = 0.0):
    return store.calculate_pricing_breakdown(service_type, distance_km, 1.0)


@router.get("/config/{service_type}")
async def get_pricing_config(service_type: str):
    config = store.get_pricing_config(service_type)
    if not config:
        raise HTTPException(status_code=404, detail="Pricing config not found")
    return config


@router.put("/config")
async def update_pricing_config(payload: PricingConfigRequest, _admin=Depends(require_role("admin"))):
    return store.upsert_pricing_config(payload.service_type, payload.base_price, payload.per_km_rate, payload.floor_price, payload.ceiling_price)
