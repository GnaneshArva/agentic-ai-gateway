from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class PolicyResult(BaseModel):
    policy_name: str
    passed: bool
    reason: Optional[str] = None
    status_code: int = 200
    retryable: bool = False
    details: Dict[str, Any] = Field(default_factory=dict)


class RateLimitResult(BaseModel):
    allowed: bool
    limit: int
    current: int
    remaining: int
    reset_seconds: float = 60.0


class TokenQuotaResult(BaseModel):
    allowed: bool
    estimated_tokens: int
    daily_quota: int
    daily_used: int
    monthly_quota: int
    monthly_used: int


class BudgetResult(BaseModel):
    allowed: bool
    estimated_cost_usd: float
    daily_budget_usd: float
    daily_spent_usd: float
    monthly_budget_usd: float
    monthly_spent_usd: float


class CircuitBreakerResult(BaseModel):
    allowed: bool
    state: str  # CLOSED, OPEN, HALF_OPEN
    failure_count: int = 0
    failure_threshold: int = 5


class ValidationResult(BaseModel):
    valid: bool
    errors: list[str] = Field(default_factory=list)
