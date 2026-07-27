from app.factories import PolicyFactory, RouterFactory, StrategyFactory, ValidatorFactory


def test_policy_factory(test_settings):
    policies = PolicyFactory.create_policies(test_settings)
    assert len(policies) == 7
    names = [p.name for p in policies]
    assert "RateLimitPolicy" in names
    assert "TokenQuotaPolicy" in names


def test_router_factory(test_settings):
    router = RouterFactory.create_router(test_settings)
    assert router is not None


def test_strategy_factory(test_settings):
    routing_strat = StrategyFactory.create_routing_strategy("priority")
    assert routing_strat is not None

    retry_strat = StrategyFactory.create_retry_strategy(test_settings)
    assert retry_strat is not None

    circuit_breaker = StrategyFactory.create_circuit_breaker(test_settings)
    assert circuit_breaker is not None


def test_validator_factory():
    validator = ValidatorFactory.create_validator()
    assert validator is not None
