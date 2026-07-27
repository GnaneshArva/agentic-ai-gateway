# Enterprise AI Gateway (`agentic-ai-gateway`)

[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111.0%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Pydantic v2](https://img.shields.io/badge/Pydantic-v2.0%2B-red.svg)](https://docs.pydantic.dev/)

**`agentic-ai-gateway`** is the central front-door microservice for the Enterprise AI Platform. Operating at the boundary of all AI workloads, it provides centralized request validation, policy governance (rate limits, token quotas, cost budgets, allowed models/providers, streaming rules), model and service routing, resiliency (retries, circuit breaking, fallback routes), correlation identifier propagation, and seamless telemetry publishing to `agentic-ai-observability`.

---

## 1. Project Overview

The AI Gateway serves as the single entry point for all enterprise AI applications. It abstracts model providers, enforces security and compliance policies, and orchestrates traffic before forwarding requests to downstream AI services like `travel-agent-service`.

### Core Responsibilities
* **AI Request Validation**: Immediate validation of payload schemas, message limits, and supported operations.
* **Policy Governance Engine**: Independent, concurrent policy evaluation for rate limits, token quotas, cost budgets, allowed models, allowed providers, payload sizes, and streaming compatibility.
* **Model & Route Selection**: Strategy-driven routing (Static, Rule-based, Priority, Weighted) across AI providers and services.
* **Resiliency & Fault Tolerance**: Retry policies with backoff strategies and circuit breaker state management (CLOSED, OPEN, HALF_OPEN).
* **Correlation & Observability**: Propagates `X-Request-ID`, `X-Trace-ID`, `X-Correlation-ID` headers and asynchronously publishes telemetry to `agentic-ai-observability` with failure isolation.
* **Streaming Proxy**: Transparent token streaming forwarder without buffering full responses.

---

## 2. AI Gateway Architecture

```text
                               Client Request
                                     │
                                     ▼
                          FastAPI Gateway Controller
                                     │
                                     ▼
                            Gateway Middleware
                   (Correlation, Logging, Telemetry)
                                     │
                                     ▼
                            Gateway Engine Facade
                                     │
     ┌───────────────────────────────┼───────────────────────────────┐
     ▼                               ▼                               ▼
Validation Layer               Request Enricher              Guardrails Client
 (RequestValidator)         (Context & Identifiers)          (agentic-ai-guardrails)
     │                               │                               │
     └───────────────────────────────┼───────────────────────────────┘
                                     ▼
                          Concurrent Policy Engine
                        (asyncio.gather Execution)
   ┌───────────────┬───────────────┬───────────────┬───────────────┬───────────────┐
   ▼               ▼               ▼               ▼               ▼               ▼
Rate Limit    Token Quota     Cost Budget   Allowed Model  Allowed Provider Request Size
   │               │               │               │               │               │
   └───────────────┴───────────────┴───────────────┴───────────────┴───────────────┘
                                     ▼
                               Routing Engine
                       (Static / Rule / Priority)
                                     │
                                     ▼
                           Downstream Forwarder
                   (Retry, Circuit Breaker, Fallbacks)
                                     │
                                     ▼
                           Downstream AI Service
                           (travel-agent-service)
                                     │
                                     ▼
                             Response Processor
                           (Metadata Enrichment)
                                     │
                    ┌────────────────┴────────────────┐
                    ▼                                 ▼
             HTTP Response                   Observability Client
                                         (agentic-ai-observability)
```

---

## 3. End-to-End Request Lifecycle

Every incoming request follows a deterministic 10-stage processing sequence:

1. **HTTP Ingestion**: Controller receives request at `POST /api/v1/gateway/process` or `/stream`.
2. **Correlation & Logging**: Middleware generates or extracts `X-Request-ID`, `X-Trace-ID`, and `X-Correlation-ID`.
3. **Payload Validation**: `RequestValidator` validates payload structures and parameters.
4. **Context Enrichment**: `RequestEnricher` populates system environment, timestamps, and metadata.
5. **Guardrails Execution**: `GuardrailsClient` delegates input security checks to `agentic-ai-guardrails`.
6. **Concurrent Policy Engine**: Evaluates independent policies concurrently using `asyncio.gather()`.
7. **Downstream Routing**: `Router` selects target endpoint based on active `RoutingStrategy`.
8. **Request Forwarding**: `DownstreamForwarder` handles HTTP dispatch with circuit breaking and retries.
9. **Response Normalization**: `ResponseProcessor` enriches response with processing duration, tokens, cost, and metadata.
10. **Telemetry Publication**: Asynchronously publishes lifecycle events to `agentic-ai-observability` with failure isolation.

---

## 4. Folder Structure

```text
agentic-ai-gateway/
├── app/
│   ├── config/             # Pydantic BaseSettings & Gateway Config
│   ├── controllers/        # REST Endpoints (no business logic)
│   ├── dto/                # Pydantic v2 DTOs (Request, Response, Context, Policy, Routing)
│   ├── exceptions/         # Strongly-typed Gateway exception hierarchy
│   ├── factories/          # Strategy, Policy, Router, & Validator factories
│   ├── gateway/            # Gateway Engine facade & Request enricher
│   ├── integrations/       # Downstream, Observability & Guardrails clients
│   ├── interfaces/         # Abstract contracts for pluggable components
│   ├── middleware/         # Correlation, Logging & Telemetry HTTP middleware
│   ├── pipeline/           # Gateway processing pipeline & Chain of Responsibility
│   ├── policies/           # Independent Policy strategy implementations
│   ├── routing/            # Router implementation & route tables
│   ├── services/           # Correlation manager & Response processor
│   ├── strategies/         # Routing, Retry, Circuit Breaker, & Load Balancing strategies
│   ├── utils/              # Structured JSON logger & Token estimator
│   └── validators/         # Request schema validation
├── tests/                  # Pytest unit & integration test suite
├── .env.example            # Environment configuration template
├── .gitignore              # Git exclusion rules
├── main.py                 # FastAPI application entry point
├── pyproject.toml          # Package dependencies & configuration
└── README.md               # Architecture documentation
```

---

## 5. Technology Stack

* **Language**: Python 3.12+
* **Web Framework**: FastAPI 0.111+
* **Data Validation**: Pydantic v2 & Pydantic-Settings
* **HTTP Client**: `httpx` (async client & streaming)
* **Async Runtime**: Python `asyncio`
* **Package Manager**: `uv`

---

## 6. Request Validation

The validation layer (`RequestValidator`) verifies inbound request payloads prior to policy execution:
* Validates presence of `prompt` or `messages` list.
* Verifies `temperature` ranges (0.0 to 2.0).
* Ensures positive `max_tokens` limits.
* Checks maximum payload bytes and conversation message count boundaries.

Rejects invalid requests immediately with a standardized `VALIDATION_ERROR` response.

---

## 7. Policy Engine

The Policy Engine executes configurable gateway policies concurrently via `asyncio.gather()`:

| Policy | Description | Rejection Status |
| :--- | :--- | :--- |
| **`RateLimitPolicy`** | Enforces sliding window rate limits per user, tenant, app, or API key. | 429 Too Many Requests |
| **`TokenQuotaPolicy`** | Estimates token usage and enforces daily/monthly token quotas. | 429 Too Many Requests |
| **`BudgetPolicy`** | Estimates request cost and enforces daily/monthly cost budgets. | 429 Too Many Requests |
| **`AllowedModelPolicy`** | Ensures requested model matches the approved whitelist. | 400 Bad Request |
| **`AllowedProviderPolicy`** | Ensures target provider matches the approved whitelist. | 400 Bad Request |
| **`RequestSizePolicy`** | Validates max payload bytes and conversation message length. | 413 Payload Too Large |
| **`StreamingPolicy`** | Verifies streaming compatibility and feature flag status. | 400 Bad Request |

---

## 8. Routing Architecture

Routing is configuration-driven using interchangeable `RoutingStrategy` implementations:
* **`StaticRoutingStrategy`**: Directs traffic to configured default endpoint (`travel-agent-service`).
* **`RuleBasedRoutingStrategy`**: Evaluates request model/provider/headers to select target endpoints.
* **`PriorityRoutingStrategy`**: Routes requests to available service instances sorted by priority tier.
* **`WeightedRoutingStrategy`**: Distributes traffic probabilistically across endpoints based on configured weights.

---

## 9. Retry and Circuit Breaker

### Retry Policies
Supports `FixedDelayRetry`, `ExponentialBackoffRetry`, and `NoRetryStrategy` for retryable network or downstream failures.

### Circuit Breaker States
`SimpleCircuitBreaker` maintains service health states:
* **`CLOSED`**: Requests flow normally.
* **`OPEN`**: Requests fail fast without hitting downstream service when failure threshold is met.
* **`HALF_OPEN`**: Automatically tests downstream recovery after configured timeout window.

---

## 10. Streaming Support

The gateway supports non-buffering streaming proxy via `/api/v1/gateway/process/stream`:
* Evaluates policies prior to stream initialization.
* Uses async HTTP streaming over `httpx`.
* Transmits Server-Sent Events (SSE) `data: {chunk}\n\n` directly to clients.
* Propagates correlation headers on the streaming HTTP request.

---

## 11. Configuration

Configuration is managed via environment variables and `.env` loaded into Pydantic settings:

```env
APP_NAME=agentic-ai-gateway
PORT=8007

TRAVEL_AGENT_SERVICE_URL=http://localhost:8000
OBSERVABILITY_SERVICE_URL=http://localhost:8006
GUARDRAILS_SERVICE_URL=http://localhost:8004

RATE_LIMIT_REQUESTS_PER_MINUTE=120
DAILY_TOKEN_QUOTA=500000
DAILY_BUDGET_USD=50.0
ALLOWED_MODELS=gpt-4o,gpt-4o-mini,claude-3-5-sonnet,gemini-1.5-pro
ALLOWED_PROVIDERS=OpenAI,Anthropic,Google,Azure OpenAI

ENABLE_ROUTING=true
ENABLE_STREAMING=true
ENABLE_RETRY=true
ENABLE_CIRCUIT_BREAKER=true
ENABLE_TELEMETRY=true
ENABLE_POLICY_ENGINE=true
```

---

## 12. Integration with Other Platform Repositories

```text
Client Application
       │
       ▼
agentic-ai-gateway (Port 8007)
       │
       ├─────────────────────────┐
       ▼                         ▼
agentic-ai-guardrails   travel-agent-service (Port 8000)
    (Port 8004)                  │
                                 ▼
                      agentic-ai-observability (Port 8006)
```

1. **`travel-agent-service`**: Receives validated and enriched AI request payloads.
2. **`agentic-ai-observability`**: Receives non-blocking event telemetry for all lifecycle stages.
3. **`agentic-ai-guardrails`**: Validates input security and safety policies.

---

## 13. Adding a New Policy

To add a new gateway policy:

1. Create a class implementing `GatewayPolicyInterface` in `app/policies/new_policy.py`:
   ```python
   from app.interfaces.policy_interface import GatewayPolicyInterface
   from app.dto.policy_dto import PolicyResult

   class CustomPolicy(GatewayPolicyInterface):
       @property
       def name(self) -> str:
           return "CustomPolicy"

       async def evaluate(self, context, request) -> PolicyResult:
           return PolicyResult(policy_name=self.name, passed=True, reason="Custom check passed")
   ```
2. Register the policy in `PolicyFactory` (`app/factories/policy_factory.py`).
3. Add any necessary settings parameters to `PolicyConfig` (`app/config/settings.py`).

No modifications to the pipeline core are required.

---

## 14. Adding a New Routing Strategy

To implement a new routing strategy:

1. Create a strategy class implementing `RoutingStrategyInterface` in `app/strategies/routing_strategy.py`:
   ```python
   from app.interfaces.strategy_interface import RoutingStrategyInterface
   from app.dto.routing_dto import RouteDefinition

   class DynamicLatencyRoutingStrategy(RoutingStrategyInterface):
       async def select_route(self, routes, context, request) -> RouteDefinition:
           # Custom routing logic
           return routes[0]
   ```
2. Register the strategy name in `StrategyFactory.create_routing_strategy()`.
3. Set `ROUTING_STRATEGY=dynamic_latency` in your `.env`.

---

## 15. Local Execution Instructions

### Installation
```bash
# Install dependencies using uv
uv sync
```

### Run Tests
```bash
# Run pytest test suite
uv run pytest
```

### Run Local Server
```bash
# Start FastAPI application
uv run uvicorn main:app --reload --port 8007
```

### Sample HTTP Request
```bash
curl -X POST http://localhost:8007/api/v1/gateway/process \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user_1",
    "prompt": "Plan a 4-day itinerary for Tokyo with sushi recommendations",
    "provider": "OpenAI",
    "model": "gpt-4o",
    "temperature": 0.7
  }'
```