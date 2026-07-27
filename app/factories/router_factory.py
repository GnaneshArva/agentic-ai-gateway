from app.config.settings import Settings
from app.factories.strategy_factory import StrategyFactory
from app.interfaces.router_interface import RouterInterface
from app.routing import DefaultRouter


class RouterFactory:
    @staticmethod
    def create_router(settings: Settings) -> RouterInterface:
        strategy = StrategyFactory.create_routing_strategy(settings.routing_config.routing_strategy)
        return DefaultRouter(strategy=strategy, settings=settings)
