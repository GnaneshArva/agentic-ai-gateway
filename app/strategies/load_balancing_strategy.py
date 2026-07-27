import random
from typing import Dict, List
from app.dto.routing_dto import RouteDefinition
from app.interfaces.strategy_interface import LoadBalancingStrategyInterface


class RoundRobinStrategy(LoadBalancingStrategyInterface):
    def __init__(self):
        self._index = 0

    def select(self, instances: List[RouteDefinition]) -> RouteDefinition:
        if not instances:
            raise ValueError("No instances available for round robin load balancing")
        selected = instances[self._index % len(instances)]
        self._index += 1
        return selected


class LeastConnectionsStrategy(LoadBalancingStrategyInterface):
    def __init__(self):
        self._active_connections: Dict[str, int] = {}

    def select(self, instances: List[RouteDefinition]) -> RouteDefinition:
        if not instances:
            raise ValueError("No instances available for least connections load balancing")
        sorted_instances = sorted(
            instances, key=lambda inst: self._active_connections.get(inst.endpoint_url, 0)
        )
        return sorted_instances[0]


class WeightedStrategy(LoadBalancingStrategyInterface):
    def select(self, instances: List[RouteDefinition]) -> RouteDefinition:
        if not instances:
            raise ValueError("No instances available for weighted load balancing")
        weights = [inst.weight for inst in instances]
        return random.choices(instances, weights=weights, k=1)[0]
