import asyncio
from app.dto.request_dto import GatewayRequest
from app.dto.routing_dto import RouteDefinition
from app.routing import DefaultRouter
from app.strategies import PriorityRoutingStrategy, StaticRoutingStrategy


def test_static_router(test_settings, gateway_context):
    async def _run():
        strategy = StaticRoutingStrategy()
        router = DefaultRouter(strategy=strategy, settings=test_settings)

        req = GatewayRequest(prompt="test route", provider="OpenAI", model="gpt-4o")
        decision = await router.route(gateway_context, req)

        assert decision.target_service == "travel-agent-service"
        assert "api/v1/travel/plan" in decision.target_endpoint

    asyncio.run(_run())


def test_priority_routing_strategy(gateway_context):
    async def _run():
        routes = [
            RouteDefinition(service_name="backup-service", endpoint_url="http://localhost:8001", priority=2),
            RouteDefinition(service_name="primary-service", endpoint_url="http://localhost:8000", priority=1),
        ]
        strategy = PriorityRoutingStrategy()
        req = GatewayRequest(prompt="test priority")

        selected = await strategy.select_route(routes, gateway_context, req)
        assert selected.service_name == "primary-service"

    asyncio.run(_run())
