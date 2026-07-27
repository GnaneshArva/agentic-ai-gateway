# Implementation Plan — Enterprise AI Gateway (`agentic-ai-gateway`)

Build an **Enterprise-grade AI Gateway** using **Python 3.12+**, **FastAPI**, **Pydantic v2**, **`asyncio`**, and **`httpx`**. The AI Gateway acts as the single front-door entry point for all AI applications across the enterprise, providing centralized request validation, policy enforcement (rate limits, token quotas, cost budgets, allowed models/providers, payload size, streaming), routing, resiliency (retries, circuit breakers, fallbacks), telemetry integration with `agentic-ai-observability`, and forwarding to downstream AI services like `travel-agent-service`.

---

## 1. High-Level Architecture & Principles

- **Clean Architecture & SOLID Principles**: Decoupled layers with inward dependency flow.
- **Chain of Responsibility Pattern**: Processing pipeline executing handlers sequentially.
- **Strategy Pattern**: Pluggable strategies for routing, retry backoff, circuit breaking, load balancing, and response processing.
- **Factory Pattern**: Centralized factories for policy instantiation, routing resolution, strategy creation, and request validation.
- **Dependency Injection**: Explicit component injection without hardcoded service dependencies.
- **Async Programming & Parallel Policy Execution**: Everything is non-blocking async, with independent policies evaluated concurrently using `asyncio.gather()`.

---

## 2. Directory Structure & File Map

```text
agentic-ai-gateway/
├── app/
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py             # BaseSettings, GatewayConfig, PolicyConfig, FeatureFlags
│   ├── controllers/
│   │   ├── __init__.py
│   │   ├── gateway_controller.py   # REST endpoints: /process, /process/stream, /routes, /policies/status
│   │   └── health_controller.py    # Health & readiness endpoints: /health, /ready
│   ├── dto/
│   │   ├── __init__.py
│   │   ├── context_dto.py          # GatewayContext, RequestContext, CorrelationContext
│   │   ├── policy_dto.py           # PolicyResult, RateLimitResult, TokenQuotaResult, BudgetResult
│   │   ├── request_dto.py          # GatewayRequest, AgentRequest, StreamingRequest, MessageDTO
│   │   ├── response_dto.py         # GatewayResponse, GatewayMetadataDTO, StreamingResponseDTO
│   │   └── routing_dto.py          # RouteDefinition, RouteSelection, RoutingDecision
│   ├── exceptions/
│   │   ├── __init__.py
│   │   └── gateway_exceptions.py   # Strongly-typed GatewayException hierarchy
│   ├── factories/
│   │   ├── __init__.py
│   │   ├── policy_factory.py       # Instantiates policies based on config & feature flags
│   │   ├── router_factory.py       # Instantiates default router with routing strategy
│   │   ├── strategy_factory.py     # Instantiates routing, retry, circuit breaker & load balancers
│   │   └── validator_factory.py    # Instantiates request validator chain
│   ├── gateway/
│   │   ├── __init__.py
│   │   ├── gateway_engine.py       # Orchestration facade unifying pipeline & services
│   │   └── request_enricher.py     # Enriches context with environment, timestamps & metadata
│   ├── integrations/
│   │   ├── __init__.py
│   │   ├── downstream_forwarder.py # Async HTTP forwarder to travel-agent-service
│   │   ├── guardrails_client.py    # Security validation via agentic-ai-guardrails
│   │   └── observability_client.py # Telemetry publisher to agentic-ai-observability
│   ├── interfaces/
│   │   ├── __init__.py
│   │   ├── forwarder_interface.py
│   │   ├── pipeline_interface.py
│   │   ├── policy_interface.py
│   │   ├── response_processor_interface.py
│   │   ├── router_interface.py
│   │   ├── strategy_interface.py
│   │   └── validator_interface.py
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── correlation_middleware.py # Identifiers extraction & propagation
│   │   ├── logging_middleware.py     # Structured JSON HTTP logging
│   │   └── telemetry_middleware.py   # Metrics recording
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── gateway_pipeline.py     # Core lifecycle pipeline with parallel asyncio.gather
│   │   └── pipeline_handler.py     # Chain of Responsibility base handler
│   ├── policies/
│   │   ├── __init__.py
│   │   ├── allowed_model_policy.py    # Model whitelist check
│   │   ├── allowed_provider_policy.py # Provider whitelist check
│   │   ├── budget_policy.py           # Cost estimation & budget limit
│   │   ├── rate_limit_policy.py       # Sliding window rate limiter
│   │   ├── request_size_policy.py     # Payload size & history length limit
│   │   ├── streaming_policy.py        # Streaming permission validation
│   │   └── token_quota_policy.py      # Token estimation & daily/monthly quota
│   ├── routing/
│   │   ├── __init__.py
│   │   └── router.py               # Route table & route selection
│   ├── services/
│   │   ├── __init__.py
│   │   ├── correlation_manager.py  # Request ID, Trace ID, Correlation ID generation
│   │   └── response_processor.py   # Downstream response normalization
│   ├── strategies/
│   │   ├── __init__.py
│   │   ├── circuit_breaker_strategy.py # Simple & Sliding Window Circuit Breakers
│   │   ├── load_balancing_strategy.py  # Round Robin, Least Connections, Weighted
│   │   ├── response_strategy.py        # Standard & Streaming response formatting
│   │   ├── retry_strategy.py           # Fixed Delay & Exponential Backoff retries
│   │   └── routing_strategy.py         # Static, Rule-based, Priority, Weighted
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── logger.py               # Structured JSON logger
│   │   └── token_estimator.py      # Token count & cost estimation heuristic
│   └── validators/
│       ├── __init__.py
│       └── request_validator.py    # Payload schema & parameters validation
├── tests/
│   ├── __init__.py
│   ├── conftest.py                 # Pytest fixtures for settings & sample requests
│   ├── test_controllers.py         # Test FastAPI REST endpoints
│   ├── test_factories.py           # Test Factory instantiations
│   ├── test_pipeline.py            # Test Gateway engine & pipeline lifecycle
│   ├── test_policies.py            # Test all 7 Gateway policies
│   ├── test_routing.py             # Test Routers & Routing strategies
│   └── test_strategies.py          # Test Circuit Breakers, Retries & Load Balancers
├── .env.example
├── .gitignore
├── IMPLEMENTATION_PLAN.md
├── main.py                         # Application entrypoint
├── pyproject.toml                  # Project manifest & dependencies
├── README.md                       # Complete project documentation
└── WALKTHROUGH.md                  # Comprehensive verification & walkthrough
```

---

## 3. Core Processing Lifecycle

1. **Client Request**: Hit REST controller (`/api/v1/gateway/process`).
2. **Middleware**: Generate `X-Request-ID`, `X-Trace-ID`, `X-Correlation-ID`.
3. **Validator**: Execute schema validation (`RequestValidator`).
4. **Context Enricher**: Populate gateway context & environment.
5. **Guardrails Client**: Forward payload to `agentic-ai-guardrails`.
6. **Concurrent Policy Engine**: Evaluate all 7 policies via `asyncio.gather()`.
7. **Routing Engine**: Resolve downstream route via selected `RoutingStrategy`.
8. **Downstream Forwarder**: Dispatch async HTTP request via `httpx.AsyncClient` protected by `CircuitBreakerStrategy` and `RetryStrategy`.
9. **Response Processor**: Attach metadata (processing time, tokens, cost, policy summary).
10. **Observability Client**: Non-blocking event dispatch to `agentic-ai-observability`.
