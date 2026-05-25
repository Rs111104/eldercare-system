from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


API_MODEL_CONFIG = ConfigDict(populate_by_name=True, extra="forbid", str_strip_whitespace=True)


class Role(str, Enum):
	customer = "customer"
	worker = "worker"
	admin = "admin"


class TaskStatus(str, Enum):
	created = "created"
	assigned = "assigned"
	accepted = "accepted"
	in_progress = "in_progress"
	completed = "completed"
	cancelled = "cancelled"


class SplitType(str, Enum):
	immediate = "immediate"
	verification = "verification"


class AuthRegisterRequest(BaseModel):
	model_config = API_MODEL_CONFIG

	phone: str = Field(..., min_length=6, max_length=32, alias="phone_number")
	password: str = Field(..., min_length=6, max_length=128)
	email: Optional[str] = Field(default=None, max_length=120)
	name: str = Field(default="", max_length=100)
	address: str = Field(default="", max_length=500)
	lat: Optional[float] = None
	lng: Optional[float] = None
	service_type: Optional[str] = Field(default=None, max_length=32)
	service_types: List[str] = Field(default_factory=list, max_length=8)
	rating: float = Field(default=4.8, ge=0, le=5)
	is_verified: bool = False
	current_lat: Optional[float] = None
	current_lng: Optional[float] = None


class LoginRequest(BaseModel):
	model_config = API_MODEL_CONFIG

	phone: str = Field(..., min_length=6, max_length=32, alias="phone_number")
	password: str = Field(..., min_length=6, max_length=128)


class TaskCreateRequest(BaseModel):
	model_config = API_MODEL_CONFIG

	customer_id: Optional[str] = Field(default=None, max_length=64)
	service_type: Optional[str] = Field(default=None, max_length=32)
	task_type: Optional[str] = Field(default=None, max_length=32)
	title: str = Field(default="Service Request", min_length=1, max_length=120)
	description: str = Field(default="", min_length=0, max_length=2000)
	mode: str = Field(default="quick", max_length=32)
	urgency: Optional[float] = Field(default=None, ge=1.0, le=1.5)
	urgency_level: Optional[int] = Field(default=None, ge=1, le=5)
	location: Optional[str] = Field(default=None, max_length=500)
	location_lat: Optional[float] = None
	location_lng: Optional[float] = None
	voice_note_url: Optional[str] = Field(default=None, max_length=500)
	worker_id: Optional[str] = Field(default=None, max_length=64)
	same_day_bundle: bool = False


class TaskUpdateRequest(BaseModel):
	model_config = API_MODEL_CONFIG

	status: Optional[TaskStatus] = None
	worker_id: Optional[str] = Field(default=None, max_length=64)
	description: Optional[str] = Field(default=None, max_length=2000)
	urgency: Optional[float] = Field(default=None, ge=1.0, le=1.5)


class PricingRequest(BaseModel):
	model_config = API_MODEL_CONFIG

	service_type: str = Field(..., min_length=1, max_length=32)
	distance_km: float = Field(..., ge=0)
	urgency: float = Field(default=1.0, ge=1.0, le=1.5)
	effort_level: Optional[int] = None
	urgency_level: Optional[int] = None
	customer_id: Optional[str] = Field(default=None, max_length=64)
	same_day_bundle: bool = False


class PricingConfigRequest(BaseModel):
	model_config = API_MODEL_CONFIG

	service_type: str = Field(..., min_length=1, max_length=32)
	base_price: float = Field(..., ge=0)
	per_km_rate: float = Field(..., ge=0)
	floor_price: Optional[float] = Field(default=None, ge=0)
	ceiling_price: Optional[float] = Field(default=None, ge=0)


class WorkerLocationRequest(BaseModel):
	model_config = API_MODEL_CONFIG

	lat: float = Field(default=0.0, alias="latitude")
	lng: float = Field(default=0.0, alias="longitude")


class TrackingEventRequest(BaseModel):
	model_config = API_MODEL_CONFIG

	task_id: str = Field(..., min_length=1, max_length=64)
	worker_id: str = Field(..., min_length=1, max_length=64)
	lat: float
	lng: float
	event_type: str = Field(default="location_update", max_length=64)


class ReviewCreateRequest(BaseModel):
	model_config = API_MODEL_CONFIG

	task_id: str = Field(..., min_length=1, max_length=64)
	customer_id: str = Field(..., min_length=1, max_length=64)
	worker_id: str = Field(..., min_length=1, max_length=64)
	rating: int = Field(..., ge=1, le=5)
	comment: str = Field(default="", max_length=1000)


class WhatsAppWebhookRequest(BaseModel):
	model_config = API_MODEL_CONFIG

	phone: str = Field(..., min_length=6, max_length=32)
	message_type: str = Field(default="text", max_length=32)
	content: str = Field(default="", max_length=4000)
	task_id: Optional[str] = Field(default=None, max_length=64)


class TaskResponse(BaseModel):
	id: str
	customer_id: str
	worker_id: Optional[str] = None
	service_type: str
	status: TaskStatus
	description: str
	price: float
	urgency: float
	voice_note_url: Optional[str] = None
	created_at: str
	completed_at: Optional[str] = None


class WorkerResponse(BaseModel):
	id: str
	phone: str
	name: str
	service_type: str
	rating: float
	is_verified: bool
	current_lat: Optional[float] = None
	current_lng: Optional[float] = None
	created_at: str


class CustomerResponse(BaseModel):
	id: str
	phone: str
	name: str
	address: str = ""
	lat: Optional[float] = None
	lng: Optional[float] = None
	created_at: str


class TokenResponse(BaseModel):
	access_token: str
	refresh_token: Optional[str] = None
	token_type: str = "bearer"
	user_id: str
	user_type: str
	user: Dict[str, Any]
