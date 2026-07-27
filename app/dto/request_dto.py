from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class MessageDTO(BaseModel):
    role: str = Field(..., description="Role of the message author e.g. user, assistant, system")
    content: str = Field(..., description="Content text of the message")
    name: Optional[str] = Field(default=None, description="Optional author identifier")


class GatewayRequest(BaseModel):
    user_id: Optional[str] = Field(default="anonymous", description="User ID for rate limiting & metrics")
    tenant_id: Optional[str] = Field(default="default", description="Tenant identifier for multi-tenancy")
    app_id: Optional[str] = Field(default="default_app", description="Client application ID")
    api_key: Optional[str] = Field(default=None, description="API Key")
    session_id: Optional[str] = Field(default=None, description="Session ID")
    conversation_id: Optional[str] = Field(default=None, description="Conversation thread ID")
    
    prompt: Optional[str] = Field(default=None, description="Input text prompt")
    messages: Optional[List[MessageDTO]] = Field(default_factory=list, description="Conversation messages")
    
    provider: Optional[str] = Field(default="OpenAI", description="Target AI Provider")
    model: Optional[str] = Field(default="gpt-4o", description="Target model name")
    
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=4096, ge=1, le=128000)
    stream: bool = Field(default=False, description="Whether to stream response tokens")
    
    target_service: Optional[str] = Field(default=None, description="Explicit target downstream service name")
    headers: Dict[str, str] = Field(default_factory=dict, description="Inbound HTTP headers")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom request payload metadata")


class AgentRequest(BaseModel):
    prompt: str
    messages: List[MessageDTO] = Field(default_factory=list)
    user_id: str = "anonymous"
    session_id: Optional[str] = None
    conversation_id: Optional[str] = None
    model: str = "gpt-4o"
    temperature: float = 0.7
    max_tokens: int = 4096
    metadata: Dict[str, Any] = Field(default_factory=dict)


class StreamingRequest(BaseModel):
    prompt: str
    messages: List[MessageDTO] = Field(default_factory=list)
    model: str = "gpt-4o"
    user_id: str = "anonymous"
    session_id: Optional[str] = None
    conversation_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RoutingRequest(BaseModel):
    provider: str
    model: str
    target_service: Optional[str] = None
    headers: Dict[str, str] = Field(default_factory=dict)


class ValidationRequest(BaseModel):
    prompt: Optional[str] = None
    messages: List[MessageDTO] = Field(default_factory=list)
    model: Optional[str] = None
    provider: Optional[str] = None
    stream: bool = False
    payload_size_bytes: int = 0
