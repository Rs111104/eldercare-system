from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


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
	model_config = ConfigDict(populate_by_name=True, extra="allow")

	phone: str = Field(..., min_length=6, alias="phone_number")
	password: str = Field(..., min_length=6)
	name: str = ""
	address: str = ""
	lat: Optional[float] = None
	lng: Optional[float] = None
	service_type: Optional[str] = None
	service_types: List[str] = Field(default_factory=list)
	rating: float = 4.8
	is_verified: bool = False
	current_lat: Optional[float] = None
	current_lng: Optional[float] = None


class LoginRequest(BaseModel):
	model_config = ConfigDict(populate_by_name=True, extra="allow")

	phone: str = Field(..., min_length=6, alias="phone_number")
	password: str = Field(..., min_length=6)


class TaskCreateRequest(BaseModel):
	model_config = ConfigDict(populate_by_name=True, extra="allow")

	customer_id: Optional[str] = None
	service_type: Optional[str] = None
	task_type: Optional[str] = None
	title: str = "Service Request"
	description: str = Field(default="", min_length=0)
	mode: str = "quick"
	urgency: Optional[float] = Field(default=None, ge=1.0, le=1.5)
	urgency_level: Optional[int] = Field(default=None, ge=1, le=5)
	location: Optional[str] = None
	location_lat: Optional[float] = None
	location_lng: Optional[float] = None
	voice_note_url: Optional[str] = None
	worker_id: Optional[str] = None
	same_day_bundle: bool = False


class TaskUpdateRequest(BaseModel):
	status: Optional[TaskStatus] = None
	worker_id: Optional[str] = None
	description: Optional[str] = None
	urgency: Optional[float] = Field(default=None, ge=1.0, le=1.5)


class PricingRequest(BaseModel):
	model_config = ConfigDict(populate_by_name=True, extra="allow")

	service_type: str
	distance_km: float = Field(..., ge=0)
	urgency: float = Field(default=1.0, ge=1.0, le=1.5)
	effort_level: Optional[int] = None
	urgency_level: Optional[int] = None
	customer_id: Optional[str] = None
	same_day_bundle: bool = False


class PricingConfigRequest(BaseModel):
	service_type: str
	base_price: float = Field(..., ge=0)
	per_km_rate: float = Field(..., ge=0)
	floor_price: Optional[float] = Field(default=None, ge=0)
	ceiling_price: Optional[float] = Field(default=None, ge=0)


class WorkerLocationRequest(BaseModel):
	model_config = ConfigDict(populate_by_name=True, extra="allow")

	lat: float = Field(default=0.0, alias="latitude")
	lng: float = Field(default=0.0, alias="longitude")


class TrackingEventRequest(BaseModel):
	task_id: str
	worker_id: str
	lat: float
	lng: float
	event_type: str = "location_update"


class ReviewCreateRequest(BaseModel):
	task_id: str
	customer_id: str
	worker_id: str
	rating: int = Field(..., ge=1, le=5)
	comment: str = ""


class WhatsAppWebhookRequest(BaseModel):
	phone: str
	message_type: str = "text"
	content: str
	task_id: Optional[str] = None


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
