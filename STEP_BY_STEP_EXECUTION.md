# Step-by-Step Execution Architecture (`agentic-ai-gateway`)

## Purpose
`agentic-ai-gateway` is the enterprise front-door firewall and API router. It operates at the network edge to enforce security, rate limits, token quotas, cost budgets, and model routing rules before requests reach downstream services like `travel-agent-service`.

---

## Step-by-Step Request Execution Flow

```
Client Request ──► [1. Telemetry] ──► [2. Validation] ──► [3. Enrichment] ──► [4. Edge Guardrail] ──► [5. Policy Engine] ──► [6. Routing] ──► [7. Resilient Forwarder] ──► Downstream Microservice
```

### Step 1: Request Ingestion & Trace Correlation
- Client sends an HTTP request to `POST /api/v1/gateway/process`.
- The gateway extracts or generates trace headers (`X-Request-ID`, `X-Trace-ID`, `X-Correlation-ID`) via `CorrelationManager`.
- Asynchronously publishes a `RequestReceived` telemetry event to `agentic-ai-observability`.

### Step 2: Payload Schema Validation (`RequestValidator`)
- Validates the structural completeness of `GatewayRequest` (checks prompt text, model name, max token bounds).
- Throws `ValidationException` (HTTP 422) if required fields are missing or invalid.

### Step 3: Request Context Enrichment (`RequestEnricher`)
- Attaches user context, session attributes, environment configurations, and correlation tokens to create `GatewayContext`.

### Step 4: Edge Guardrail Validation (`GuardrailsClient`)
- Calls `agentic-ai-guardrails` microservice (`POST /guardrails/input/validate`).
- **Perimeter Security**: Checks for prompt injection (`"ignore instructions"`), jailbreaks, and inbound PII.
- If blocked $\rightarrow$ raises `PolicyException` (`HTTP 400 Bad Request`) immediately to halt execution before consuming downstream resources.
- If allowed $\rightarrow$ updates request with sanitized/masked prompt text if PII was detected.

### Step 5: Concurrent Governance Policy Engine (`asyncio.gather`)
Executes 6 policies in parallel:
1. `RequestSizePolicy`: Enforces payload byte limits.
2. `RateLimitPolicy`: Checks requests-per-minute (RPM) bucket per user/session.
3. `TokenQuotaPolicy`: Enforces daily token usage quotas.
4. `CostBudgetPolicy`: Checks accumulated USD budget limits.
5. `AllowedModelPolicy`: Verifies requested model (e.g., `gpt-4o`) is allowed.
6. `AllowedProviderPolicy`: Restricts allowed AI providers (e.g., OpenAI vs Anthropic).

If any policy fails $\rightarrow$ throws `PolicyException` with exact failure details (e.g., HTTP 429 Too Many Requests).

### Step 6: Strategy-Driven Routing (`RouterEngine`)
- Evaluates configured routing strategy (Static, Rule-based, Priority, Weighted).
- Maps target endpoint (e.g., forwards request to `travel-agent-service` at `http://localhost:8000/api/v1/travel/plan`).

### Step 7: Resilient Downstream Forwarding (`DownstreamForwarder`)
- Wraps the downstream request in resiliency patterns:
  - **Circuit Breaker**: Checks circuit state (`CLOSED`, `OPEN`, `HALF_OPEN`). Halts request if circuit is `OPEN`.
  - **Retry with Backoff**: Retries transient network failures.
- Forwards payload to target downstream microservice.

### Step 8: Response Processing & Final Telemetry
- Receives response from downstream microservice.
- Formats payload via `ResponseProcessor`.
- Publishes `RequestCompleted` event to `agentic-ai-observability` and returns `GatewayResponse` to client.
