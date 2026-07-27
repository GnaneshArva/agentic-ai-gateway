from functools import lru_cache
from typing import List, Union
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class GatewayConfig(BaseModel):
    app_name: str = "agentic-ai-gateway"
    app_env: str = "development"
    log_level: str = "INFO"
    port: int = 8007
    gateway_version: str = "1.0.0"
    gateway_timeout_seconds: float = 60.0
    downstream_timeout_seconds: float = 45.0
    streaming_timeout_seconds: float = 120.0
    travel_agent_service_url: str = "http://localhost:8000"
    observability_service_url: str = "http://localhost:8006"
    guardrails_service_url: str = "http://localhost:8004"


class PolicyConfig(BaseModel):
    rate_limit_requests_per_minute: int = 120
    daily_token_quota: int = 500000
    monthly_token_quota: int = 10000000
    request_token_limit: int = 32000
    daily_budget_usd: float = 50.0
    monthly_budget_usd: float = 1000.0
    max_payload_bytes: int = 10485760  # 10MB
    max_attachment_bytes: int = 5242880  # 5MB
    max_conversation_history: int = 50
    allowed_models: List[str] = [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4",
        "gpt-3.5-turbo",
        "claude-3-5-sonnet",
        "claude-3-haiku",
        "gemini-1.5-pro",
        "gemini-1.5-flash",
    ]
    allowed_providers: List[str] = [
        "OpenAI",
        "Anthropic",
        "Google",
        "Azure OpenAI",
    ]


class RoutingConfig(BaseModel):
    default_route: str = "travel-agent-service"
    routing_strategy: str = "static"  # static, rule_based, priority, weighted
    fallback_route: str = "travel-agent-service"


class RetryConfig(BaseModel):
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    backoff_strategy: str = "exponential"  # fixed, exponential, none


class CircuitBreakerConfig(BaseModel):
    failure_threshold: int = 5
    recovery_timeout_seconds: float = 30.0


class FeatureFlags(BaseModel):
    enable_routing: bool = True
    enable_streaming: bool = True
    enable_retry: bool = True
    enable_circuit_breaker: bool = True
    enable_telemetry: bool = True
    enable_policy_engine: bool = True
    enable_guardrails: bool = True


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_nested_delimiter="__",
    )

    # General App settings
    app_name: str = Field(default="agentic-ai-gateway", validation_alias="APP_NAME")
    app_env: str = Field(default="development", validation_alias="APP_ENV")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    port: int = Field(default=8007, validation_alias="PORT")

    # Service URLs
    travel_agent_service_url: str = Field(
        default="http://localhost:8000", validation_alias="TRAVEL_AGENT_SERVICE_URL"
    )
    observability_service_url: str = Field(
        default="http://localhost:8006", validation_alias="OBSERVABILITY_SERVICE_URL"
    )
    guardrails_service_url: str = Field(
        default="http://localhost:8004", validation_alias="GUARDRAILS_SERVICE_URL"
    )

    # Gateway timeouts
    gateway_timeout_seconds: float = Field(
        default=60.0, validation_alias="GATEWAY_TIMEOUT_SECONDS"
    )
    downstream_timeout_seconds: float = Field(
        default=45.0, validation_alias="DOWNSTREAM_TIMEOUT_SECONDS"
    )
    streaming_timeout_seconds: float = Field(
        default=120.0, validation_alias="STREAMING_TIMEOUT_SECONDS"
    )

    # Policy Settings
    rate_limit_requests_per_minute: int = Field(
        default=120, validation_alias="RATE_LIMIT_REQUESTS_PER_MINUTE"
    )
    daily_token_quota: int = Field(
        default=500000, validation_alias="DAILY_TOKEN_QUOTA"
    )
    monthly_token_quota: int = Field(
        default=10000000, validation_alias="MONTHLY_TOKEN_QUOTA"
    )
    request_token_limit: int = Field(
        default=32000, validation_alias="REQUEST_TOKEN_LIMIT"
    )
    daily_budget_usd: float = Field(
        default=50.0, validation_alias="DAILY_BUDGET_USD"
    )
    monthly_budget_usd: float = Field(
        default=1000.0, validation_alias="MONTHLY_BUDGET_USD"
    )
    max_payload_bytes: int = Field(
        default=10485760, validation_alias="MAX_PAYLOAD_BYTES"
    )

    # Whitelists as CSV or List
    allowed_models_raw: str = Field(
        default="gpt-4o,gpt-4o-mini,gpt-4,gpt-3.5-turbo,claude-3-5-sonnet,claude-3-haiku,gemini-1.5-pro,gemini-1.5-flash",
        validation_alias="ALLOWED_MODELS",
    )
    allowed_providers_raw: str = Field(
        default="OpenAI,Anthropic,Google,Azure OpenAI",
        validation_alias="ALLOWED_PROVIDERS",
    )

    # Routing settings
    default_route: str = Field(
        default="travel-agent-service", validation_alias="DEFAULT_ROUTE"
    )
    routing_strategy: str = Field(
        default="static", validation_alias="ROUTING_STRATEGY"
    )

    # Resilience settings
    max_retries: int = Field(default=3, validation_alias="MAX_RETRIES")
    retry_delay_seconds: float = Field(
        default=1.0, validation_alias="RETRY_DELAY_SECONDS"
    )
    backoff_strategy: str = Field(
        default="exponential", validation_alias="BACKOFF_STRATEGY"
    )
    circuit_failure_threshold: int = Field(
        default=5, validation_alias="CIRCUIT_FAILURE_THRESHOLD"
    )
    circuit_recovery_timeout_seconds: float = Field(
        default=30.0, validation_alias="CIRCUIT_RECOVERY_TIMEOUT_SECONDS"
    )

    # Feature Flags
    enable_routing: bool = Field(default=True, validation_alias="ENABLE_ROUTING")
    enable_streaming: bool = Field(default=True, validation_alias="ENABLE_STREAMING")
    enable_retry: bool = Field(default=True, validation_alias="ENABLE_RETRY")
    enable_circuit_breaker: bool = Field(
        default=True, validation_alias="ENABLE_CIRCUIT_BREAKER"
    )
    enable_telemetry: bool = Field(
        default=True, validation_alias="ENABLE_TELEMETRY"
    )
    enable_policy_engine: bool = Field(
        default=True, validation_alias="ENABLE_POLICY_ENGINE"
    )
    enable_guardrails: bool = Field(
        default=True, validation_alias="ENABLE_GUARDRAILS"
    )

    @property
    def allowed_models(self) -> List[str]:
        if isinstance(self.allowed_models_raw, list):
            return self.allowed_models_raw
        return [m.strip() for m in self.allowed_models_raw.split(",") if m.strip()]

    @property
    def allowed_providers(self) -> List[str]:
        if isinstance(self.allowed_providers_raw, list):
            return self.allowed_providers_raw
        return [p.strip() for p in self.allowed_providers_raw.split(",") if p.strip()]

    @property
    def gateway_config(self) -> GatewayConfig:
        return GatewayConfig(
            app_name=self.app_name,
            app_env=self.app_env,
            log_level=self.log_level,
            port=self.port,
            gateway_timeout_seconds=self.gateway_timeout_seconds,
            downstream_timeout_seconds=self.downstream_timeout_seconds,
            streaming_timeout_seconds=self.streaming_timeout_seconds,
            travel_agent_service_url=self.travel_agent_service_url,
            observability_service_url=self.observability_service_url,
            guardrails_service_url=self.guardrails_service_url,
        )

    @property
    def policy_config(self) -> PolicyConfig:
        return PolicyConfig(
            rate_limit_requests_per_minute=self.rate_limit_requests_per_minute,
            daily_token_quota=self.daily_token_quota,
            monthly_token_quota=self.monthly_token_quota,
            request_token_limit=self.request_token_limit,
            daily_budget_usd=self.daily_budget_usd,
            monthly_budget_usd=self.monthly_budget_usd,
            max_payload_bytes=self.max_payload_bytes,
            allowed_models=self.allowed_models,
            allowed_providers=self.allowed_providers,
        )

    @property
    def routing_config(self) -> RoutingConfig:
        return RoutingConfig(
            default_route=self.default_route,
            routing_strategy=self.routing_strategy,
        )

    @property
    def retry_config(self) -> RetryConfig:
        return RetryConfig(
            max_retries=self.max_retries,
            retry_delay_seconds=self.retry_delay_seconds,
            backoff_strategy=self.backoff_strategy,
        )

    @property
    def circuit_breaker_config(self) -> CircuitBreakerConfig:
        return CircuitBreakerConfig(
            failure_threshold=self.circuit_failure_threshold,
            recovery_timeout_seconds=self.circuit_recovery_timeout_seconds,
        )

    @property
    def feature_flags(self) -> FeatureFlags:
        return FeatureFlags(
            enable_routing=self.enable_routing,
            enable_streaming=self.enable_streaming,
            enable_retry=self.enable_retry,
            enable_circuit_breaker=self.enable_circuit_breaker,
            enable_telemetry=self.enable_telemetry,
            enable_policy_engine=self.enable_policy_engine,
            enable_guardrails=self.enable_guardrails,
        )


@lru_cache()
def get_settings() -> Settings:
    return Settings()
