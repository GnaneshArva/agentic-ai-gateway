from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class GatewayMetadataDTO(BaseModel):
    request_id: str
    trace_id: str
    correlation_id: str
    gateway_version: str = "1.0.0"
    environment: str = "development"
    processing_time_ms: float = 0.0
    target_service: Optional[str] = None
    target_endpoint: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    tokens_used: int = 0
    cost_usd: float = 0.0
    policy_results_summary: Dict[str, str] = Field(default_factory=dict)


class GatewayResponse(BaseModel):
    success: bool = True
    status_code: int = 200
    message: str = "Request processed successfully"
    data: Optional[Dict[str, Any]] = None
    metadata: Optional[GatewayMetadataDTO] = None
    error: Optional[Dict[str, Any]] = None


class AgentResponse(BaseModel):
    success: bool = True
    result: Any = None
    messages: Any = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class StreamingResponseDTO(BaseModel):
    chunk: str
    is_final: bool = False
    metadata: Optional[GatewayMetadataDTO] = None


class ErrorResponse(BaseModel):
    error_code: str
    message: str
    status_code: int = 400
    retryable: bool = False
    component: str = "agentic-ai-gateway"
    details: Optional[Dict[str, Any]] = None
    metadata: Optional[GatewayMetadataDTO] = None


class RoutingResponse(BaseModel):
    target_service: str
    target_endpoint: str
    routing_strategy: str
    weight: float = 1.0
    headers: Dict[str, str] = Field(default_factory=dict)
