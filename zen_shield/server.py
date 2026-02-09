"""
Zen Shield Server - FastAPI microservice for data sanitization
"""

import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .sanitizer import ZenSanitizer
from .schemas import HealthStatus, SanitizerRequest, SanitizerResponse

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Global sanitizer instance
sanitizer: Optional[ZenSanitizer] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    global sanitizer

    # Startup
    logger.info("Starting Zen Shield Server...")
    sanitizer = ZenSanitizer(
        small_llm_endpoint="http://localhost:8001",
        enable_compression=True,
        enable_injection_detection=True,
    )
    logger.info("Zen Shield initialized")

    yield

    # Shutdown
    logger.info("Shutting down Zen Shield Server...")


app = FastAPI(
    title="Zen Shield - Security Sanitizer",
    description="Data sanitization service for pentesting tools",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthStatus)
async def health_check():
    """Health check endpoint"""
    if not sanitizer:
        raise HTTPException(status_code=503, detail="Sanitizer not initialized")

    health = await sanitizer.health_check()
    return HealthStatus(
        status=health["status"],
        small_llm_available=health["small_llm"] == "available",
        circuit_breaker_state=health["circuit_breaker"],
        active_filters=[
            "secret_scrubber",
            "injection_detector" if health["injection_detector"] == "active" else None,
            "context_compressor",
        ],
        version="1.0.0",
    )


@app.post("/sanitize", response_model=SanitizerResponse)
async def sanitize_data(request: SanitizerRequest):
    """
    Sanitize raw data for safe LLM processing

    This endpoint:
    1. Detects and masks secrets (API keys, tokens, passwords)
    2. Checks for prompt injection attempts
    3. Compresses context to reduce token costs
    4. Returns cleaned data with metadata
    """
    if not sanitizer:
        raise HTTPException(status_code=503, detail="Sanitizer not initialized")

    try:
        response = await sanitizer.process(request)
        return response
    except Exception as e:
        logger.error(f"Sanitization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sanitize/quick")
async def quick_scrub(text: str):
    """
    Quick scrub - only secret removal, no compression

    Useful for simple cases where speed is priority.
    """
    if not sanitizer:
        raise HTTPException(status_code=503, detail="Sanitizer not initialized")

    cleaned = await sanitizer.quick_scrub(text)
    return {"cleaned_data": cleaned}


@app.get("/stats")
async def get_stats():
    """Get sanitizer statistics"""
    if not sanitizer:
        raise HTTPException(status_code=503, detail="Sanitizer not initialized")

    return sanitizer.get_stats()


@app.post("/reset")
async def reset_circuit_breaker():
    """Reset circuit breaker to closed state"""
    if not sanitizer:
        raise HTTPException(status_code=503, detail="Sanitizer not initialized")

    await sanitizer.circuit_breaker.force_reset()
    return {"message": "Circuit breaker reset to CLOSED"}


# Batch processing endpoint
class BatchSanitizeRequest(BaseModel):
    """Batch sanitization request"""

    items: list[SanitizerRequest]
    continue_on_error: bool = True


@app.post("/sanitize/batch")
async def sanitize_batch(request: BatchSanitizeRequest):
    """
    Process multiple items in batch

    Useful for processing multiple scan results at once.
    """
    if not sanitizer:
        raise HTTPException(status_code=503, detail="Sanitizer not initialized")

    results = []
    errors = []

    for i, item in enumerate(request.items):
        try:
            result = await sanitizer.process(item)
            results.append(result)
        except Exception as e:
            logger.error(f"Batch item {i} failed: {e}")
            errors.append({"index": i, "error": str(e)})
            if not request.continue_on_error:
                break

    return {
        "successful": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9000)
