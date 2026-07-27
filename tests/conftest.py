import pytest
from app.config.settings import Settings
from app.dto.context_dto import GatewayContext
from app.dto.request_dto import GatewayRequest
from app.services.correlation_manager import CorrelationManager


@pytest.fixture
def test_settings():
    return Settings(
        APP_NAME="agentic-ai-gateway-test",
        APP_ENV="testing",
        RATE_LIMIT_REQUESTS_PER_MINUTE=5,
        DAILY_TOKEN_QUOTA=500000,
        DAILY_BUDGET_USD=50.0,
        REQUEST_TOKEN_LIMIT=32000,
        MAX_PAYLOAD_BYTES=10000000,
        ALLOWED_MODELS="gpt-4o,gpt-4o-mini,claude-3-5-sonnet",
        ALLOWED_PROVIDERS="OpenAI,Anthropic,Google",
    )


@pytest.fixture
def sample_request():
    return GatewayRequest(
        user_id="user_123",
        tenant_id="tenant_abc",
        prompt="Plan a 3-day trip to Tokyo",
        provider="OpenAI",
        model="gpt-4o",
        temperature=0.7,
        max_tokens=2000,
    )


@pytest.fixture
def gateway_context(test_settings, sample_request):
    manager = CorrelationManager(test_settings)
    return manager.create_context(sample_request)
