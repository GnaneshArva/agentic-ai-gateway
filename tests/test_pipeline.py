import asyncio
import pytest
from app.dto.request_dto import GatewayRequest
from app.exceptions.gateway_exceptions import PolicyException, ValidationException
from app.gateway.gateway_engine import GatewayEngine


def test_gateway_engine_end_to_end(test_settings):
    async def _run():
        engine = GatewayEngine(test_settings)
        req = GatewayRequest(
            user_id="user_test",
            prompt="Plan a trip to Paris",
            provider="OpenAI",
            model="gpt-4o",
        )

        response = await engine.process_request(req)
        assert response.success is True
        assert response.status_code == 200
        assert response.metadata is not None
        assert response.metadata.request_id is not None
        assert response.metadata.target_service == "travel-agent-service"

    asyncio.run(_run())


def test_gateway_engine_validation_error(test_settings):
    async def _run():
        engine = GatewayEngine(test_settings)
        invalid_req = GatewayRequest(prompt=None, messages=[])

        with pytest.raises(ValidationException):
            await engine.process_request(invalid_req)

    asyncio.run(_run())


def test_gateway_engine_policy_error(test_settings):
    async def _run():
        engine = GatewayEngine(test_settings)
        policy_violating_req = GatewayRequest(prompt="hello", model="forbidden-model")

        with pytest.raises(PolicyException):
            await engine.process_request(policy_violating_req)

    asyncio.run(_run())
