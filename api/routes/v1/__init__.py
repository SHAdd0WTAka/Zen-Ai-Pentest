"""
API Routes Version 1

Zen AI Pentest API v1 - Modular route definitions

## Authentication

All endpoints except health check require Bearer token authentication:
```
Authorization: Bearer <token>
```

## Rate Limiting

API requests are rate limited. Default: 100 requests per minute.

## Response Format

All responses follow the JSON:API specification where applicable.

## Error Codes

- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `429` - Rate Limited
- `500` - Internal Server Error
"""

from fastapi import APIRouter

from .auth import router as auth_router
from .findings import router as findings_router
from .health import router as health_router
from .metrics import router as metrics_router
from .notifications import router as notifications_router
from .openapi_tags import OPENAPI_TAGS
from .reports import router as reports_router
from .scans import router as scans_router
from .schedules import router as schedules_router
from .settings import router as settings_router
from .stats import router as stats_router
from .tools import router as tools_router
from .websocket import router as websocket_router

# Create main v1 router with metadata
api_v1_router = APIRouter(
    prefix="/api/v1",
    tags=["v1"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"},
    },
)

# Include all sub-routers with their tags
# Note: Each router already defines its own prefix
api_v1_router.include_router(auth_router, tags=["Authentication"])
api_v1_router.include_router(scans_router, tags=["Scans"])
api_v1_router.include_router(findings_router, tags=["Findings"])
api_v1_router.include_router(tools_router, tags=["Tools"])
api_v1_router.include_router(reports_router, tags=["Reports"])
api_v1_router.include_router(schedules_router, tags=["Schedules"])
api_v1_router.include_router(settings_router, tags=["Settings"])
api_v1_router.include_router(notifications_router, tags=["Notifications"])
api_v1_router.include_router(stats_router, tags=["Statistics"])
api_v1_router.include_router(health_router, tags=["Health"])
api_v1_router.include_router(metrics_router, tags=["Metrics"])
api_v1_router.include_router(websocket_router, tags=["WebSocket"])

__all__ = ["api_v1_router", "OPENAPI_TAGS"]
