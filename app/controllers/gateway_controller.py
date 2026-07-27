from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from app.config.settings import Settings, get_settings
from app.dto.request_dto import GatewayRequest
from app.dto.response_dto import GatewayResponse
from app.gateway.gateway_engine import GatewayEngine

router = APIRouter(prefix="/api/v1/gateway", tags=["AI Gateway"])

# Global engine instance or dependency-injected instance
_engine_instance = None


def get_gateway_engine(settings: Settings = Depends(get_settings)) -> GatewayEngine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = GatewayEngine(settings)
    return _engine_instance


@router.post("/process", response_model=GatewayResponse)
async def process_request(
    request_payload: GatewayRequest,
    raw_request: Request,
    engine: GatewayEngine = Depends(get_gateway_engine),
):
    headers = dict(raw_request.headers)
    return await engine.process_request(request_payload, headers)


@router.post("/process/stream")
async def process_stream(
    request_payload: GatewayRequest,
    raw_request: Request,
    engine: GatewayEngine = Depends(get_gateway_engine),
):
    headers = dict(raw_request.headers)
    request_payload.stream = True

    async def event_generator():
        async for chunk in engine.process_stream(request_payload, headers):
            if chunk.chunk:
                yield f"data: {chunk.chunk}\n\n"
            if chunk.is_final:
                yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/routes")
async def list_routes(settings: Settings = Depends(get_settings)):
    return {
        "default_route": settings.default_route,
        "routing_strategy": settings.routing_strategy,
        "routes": [
            {
                "service_name": "travel-agent-service",
                "endpoint_url": f"{settings.travel_agent_service_url.rstrip('/')}/api/v1/travel/plan",
                "is_active": True,
            }
        ],
    }


@router.get("/policies/status")
async def policy_status(settings: Settings = Depends(get_settings)):
    return {
        "policy_engine_enabled": settings.feature_flags.enable_policy_engine,
        "active_policies": [
            "RequestSizePolicy",
            "RateLimitPolicy",
            "TokenQuotaPolicy",
            "BudgetPolicy",
            "AllowedModelPolicy",
            "AllowedProviderPolicy",
            "StreamingPolicy",
        ],
        "limits": {
            "rate_limit_rpm": settings.rate_limit_requests_per_minute,
            "daily_token_quota": settings.daily_token_quota,
            "daily_budget_usd": settings.daily_budget_usd,
            "request_token_limit": settings.request_token_limit,
            "max_payload_bytes": settings.max_payload_bytes,
            "allowed_models": settings.allowed_models,
            "allowed_providers": settings.allowed_providers,
        },
        "feature_flags": settings.feature_flags.model_dump(),
    }
