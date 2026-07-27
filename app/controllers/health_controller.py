from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from app.config.settings import Settings, get_settings

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check(settings: Settings = Depends(get_settings)):
    return {
        "status": "healthy",
        "service": settings.app_name,
        "environment": settings.app_env,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/ready")
async def readiness_check(settings: Settings = Depends(get_settings)):
    return {
        "status": "ready",
        "service": settings.app_name,
        "dependencies": {
            "travel-agent-service": settings.travel_agent_service_url,
            "agentic-ai-observability": settings.observability_service_url,
            "agentic-ai-guardrails": settings.guardrails_service_url,
        },
    }
