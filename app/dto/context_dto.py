from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from app.dto.policy_dto import PolicyResult
from app.dto.routing_dto import RoutingDecision


class RequestContext(BaseModel):
    user_id: str = "anonymous"
    tenant_id: str = "default"
    app_id: str = "default_app"
    session_id: Optional[str] = None
    conversation_id: Optional[str] = None
    client_ip: Optional[str] = None
    user_agent: Optional[str] = None


class CorrelationContext(BaseModel):
    request_id: str
    trace_id: str
    correlation_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RoutingContext(BaseModel):
    provider: str = "OpenAI"
    model: str = "gpt-4o"
    target_service: Optional[str] = None
    target_endpoint: Optional[str] = None
    routing_strategy: str = "static"
    decision: Optional[RoutingDecision] = None


class PolicyContext(BaseModel):
    policy_results: List[PolicyResult] = Field(default_factory=list)
    all_passed: bool = True
    failed_policy: Optional[str] = None
    failure_reason: Optional[str] = None


class GatewayContext(BaseModel):
    correlation: CorrelationContext
    request_info: RequestContext
    routing: RoutingContext
    policy: PolicyContext = Field(default_factory=PolicyContext)
    
    start_time_monotonic: float = 0.0
    gateway_version: str = "1.0.0"
    environment: str = "development"
    
    estimated_tokens: int = 0
    estimated_cost_usd: float = 0.0
    
    custom_attributes: Dict[str, Any] = Field(default_factory=dict)
