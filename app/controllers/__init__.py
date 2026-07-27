from app.controllers.gateway_controller import router as gateway_router
from app.controllers.health_controller import router as health_router

__all__ = ["gateway_router", "health_router"]
