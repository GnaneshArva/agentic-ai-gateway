import random
from typing import List
from app.dto.context_dto import GatewayContext
from app.dto.request_dto import GatewayRequest
from app.dto.routing_dto import RouteDefinition
from app.exceptions.gateway_exceptions import RoutingException
from app.interfaces.strategy_interface import RoutingStrategyInterface


class StaticRoutingStrategy(RoutingStrategyInterface):
    async def select_route(
        self,
        routes: List[RouteDefinition],
        context: GatewayContext,
        request: GatewayRequest,
    ) -> RouteDefinition:
        active = [r for r in routes if r.is_active]
        if not active:
            raise RoutingException("No active routes available for StaticRoutingStrategy.")

        # If target service is explicitly requested, try matching it
        if request.target_service:
            matched = [r for r in active if r.service_name == request.target_service]
            if matched:
                return matched[0]

        return active[0]


class RuleBasedRoutingStrategy(RoutingStrategyInterface):
    async def select_route(
        self,
        routes: List[RouteDefinition],
        context: GatewayContext,
        request: GatewayRequest,
    ) -> RouteDefinition:
        active = [r for r in routes if r.is_active]
        if not active:
            raise RoutingException("No active routes available for RuleBasedRoutingStrategy.")

        # Rule matching based on requested provider / model / headers
        target = request.target_service or ""
        if "travel" in target.lower() or "agent" in target.lower():
            matched = [r for r in active if "travel" in r.service_name.lower()]
            if matched:
                return matched[0]

        # Default fallback to first active route
        return active[0]


class PriorityRoutingStrategy(RoutingStrategyInterface):
    async def select_route(
        self,
        routes: List[RouteDefinition],
        context: GatewayContext,
        request: GatewayRequest,
    ) -> RouteDefinition:
        active = [r for r in routes if r.is_active]
        if not active:
            raise RoutingException("No active routes available for PriorityRoutingStrategy.")

        # Sort by priority ascending (lowest priority number = highest preference)
        sorted_routes = sorted(active, key=lambda r: r.priority)
        return sorted_routes[0]


class WeightedRoutingStrategy(RoutingStrategyInterface):
    async def select_route(
        self,
        routes: List[RouteDefinition],
        context: GatewayContext,
        request: GatewayRequest,
    ) -> RouteDefinition:
        active = [r for r in routes if r.is_active]
        if not active:
            raise RoutingException("No active routes available for WeightedRoutingStrategy.")

        weights = [r.weight for r in active]
        total_weight = sum(weights)
        if total_weight <= 0:
            return active[0]

        return random.choices(active, weights=weights, k=1)[0]
