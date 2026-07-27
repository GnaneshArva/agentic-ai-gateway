import asyncio
from app.dto.request_dto import GatewayRequest
from app.policies import (
    AllowedModelPolicy,
    AllowedProviderPolicy,
    BudgetPolicy,
    RateLimitPolicy,
    RequestSizePolicy,
    StreamingPolicy,
    TokenQuotaPolicy,
)


def test_allowed_model_policy_pass_and_fail(test_settings, gateway_context):
    async def _run():
        policy = AllowedModelPolicy(test_settings.policy_config)

        valid_req = GatewayRequest(prompt="test", model="gpt-4o")
        result_pass = await policy.evaluate(gateway_context, valid_req)
        assert result_pass.passed is True

        invalid_req = GatewayRequest(prompt="test", model="unsupported-model-9000")
        result_fail = await policy.evaluate(gateway_context, invalid_req)
        assert result_fail.passed is False
        assert result_fail.status_code == 400

    asyncio.run(_run())


def test_allowed_provider_policy_pass_and_fail(test_settings, gateway_context):
    async def _run():
        policy = AllowedProviderPolicy(test_settings.policy_config)

        valid_req = GatewayRequest(prompt="test", provider="OpenAI")
        res_pass = await policy.evaluate(gateway_context, valid_req)
        assert res_pass.passed is True

        invalid_req = GatewayRequest(prompt="test", provider="UnknownProvider")
        res_fail = await policy.evaluate(gateway_context, invalid_req)
        assert res_fail.passed is False

    asyncio.run(_run())


def test_rate_limit_policy(test_settings, gateway_context):
    async def _run():
        policy = RateLimitPolicy(test_settings.policy_config)
        req = GatewayRequest(prompt="hi", user_id="rate_user")

        for _ in range(5):
            res = await policy.evaluate(gateway_context, req)
            assert res.passed is True

        res_over = await policy.evaluate(gateway_context, req)
        assert res_over.passed is False
        assert res_over.status_code == 429

    asyncio.run(_run())


def test_token_quota_policy(test_settings, gateway_context):
    async def _run():
        policy = TokenQuotaPolicy(test_settings.policy_config)
        oversized_req = GatewayRequest(prompt="test", max_tokens=100000)
        res = await policy.evaluate(gateway_context, oversized_req)
        assert res.passed is False

    asyncio.run(_run())


def test_streaming_policy(test_settings, gateway_context):
    async def _run():
        policy = StreamingPolicy(test_settings.feature_flags)
        req = GatewayRequest(prompt="stream me", stream=True)

        res = await policy.evaluate(gateway_context, req)
        assert res.passed is True

    asyncio.run(_run())


def test_request_size_policy(test_settings, gateway_context):
    async def _run():
        policy = RequestSizePolicy(test_settings.policy_config)
        req = GatewayRequest(prompt="normal payload size")

        res = await policy.evaluate(gateway_context, req)
        assert res.passed is True

    asyncio.run(_run())
