from typing import Dict, Optional
from pydantic import BaseModel, Field


class RouteDefinition(BaseModel):
    service_name: str
    endpoint_url: str
    health_url: Optional[str] = None
    weight: float = 1.0
    priority: int = 1
    is_active: bool = True


class RoutingRule(BaseModel):
    rule_name: str
    condition_key: str  # e.g., 'model', 'provider', 'tenant_id'
    condition_value: str
    target_service: str


class RouteSelection(BaseModel):
    service_name: str
    endpoint_url: str
    strategy_used: str


class RoutingDecision(BaseModel):
    target_service: str
    target_endpoint: str
    strategy: str
    route_definition: Optional[RouteDefinition] = None
    headers: Dict[str, str] = Field(default_factory=dict)
