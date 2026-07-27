from typing import List, Optional
from app.config.settings import RoutingConfig, Settings
from app.dto.context_dto import GatewayContext
from app.dto.request_dto import GatewayRequest
from app.dto.routing_dto import RouteDefinition, RoutingDecision
from app.interfaces.router_interface import RouterInterface
from app.interfaces.strategy_interface import RoutingStrategyInterface


class DefaultRouter(RouterInterface):
    def __init__(
        self,
        strategy: RoutingStrategyInterface,
        settings: Settings,
        custom_routes: Optional[List[RouteDefinition]] = None,
    ):
        self._strategy = strategy
        self._settings = settings

        # Pre-populate registered downstream routes
        self._routes: List[RouteDefinition] = custom_routes or [
            RouteDefinition(
                service_name="travel-agent-service",
                endpoint_url=f"{settings.travel_agent_service_url.rstrip('/')}/api/v1/travel/plan",
                health_url=f"{settings.travel_agent_service_url.rstrip('/')}/health",
                priority=1,
                weight=1.0,
                is_active=True,
            ),
        ]

    async def route(
        self, context: GatewayContext, request: GatewayRequest
    ) -> RoutingDecision:
        selected_route = await self._strategy.select_route(
            self._routes, context, request
        )

        decision = RoutingDecision(
            target_service=selected_route.service_name,
            target_endpoint=selected_route.endpoint_url,
            strategy=self._settings.routing_config.routing_strategy,
            route_definition=selected_route,
            headers={
                "X-Gateway-Route": selected_route.service_name,
                "X-Target-Provider": request.provider or "OpenAI",
                "X-Target-Model": request.model or "gpt-4o",
            },
        )

        # Populate context routing info
        context.routing.target_service = selected_route.service_name
        context.routing.target_endpoint = selected_route.endpoint_url
        context.routing.routing_strategy = decision.strategy
        context.routing.decision = decision

        return decision
