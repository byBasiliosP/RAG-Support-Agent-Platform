# app/rate_limiter.py
"""
Rate limiting configuration using slowapi.
Provides configurable rate limits per endpoint type.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse


def get_client_ip(request: Request) -> str:
    """
    Get client IP address, handling proxy headers.
    Falls back to get_remote_address if no forwarded header.
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)


# Initialize limiter with custom key function
limiter = Limiter(key_func=get_client_ip)


# Rate limit configurations by endpoint type
class RateLimits:
    """Configurable rate limits for different API endpoint types"""
    
    # General API endpoints
    DEFAULT = "100/minute"
    
    # RAG/AI endpoints (more expensive, lower limit)
    RAG = "20/minute"
    
    # Voice/ElevenLabs endpoints
    VOICE = "30/minute"
    
    # Analytics endpoints
    ANALYTICS = "60/minute"
    
    # Write operations (POST, PUT, DELETE)
    WRITE = "50/minute"
    
    # Authentication endpoints (when added)
    AUTH = "5/minute"
    
    # Health check and status endpoints
    STATUS = "200/minute"


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    Custom handler for rate limit exceeded responses.
    Returns a JSON response with retry information.
    """
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "detail": str(exc.detail),
            "retry_after": getattr(exc, 'retry_after', 60),
            "message": "Too many requests. Please slow down and try again."
        },
        headers={
            "Retry-After": str(getattr(exc, 'retry_after', 60)),
            "X-RateLimit-Limit": str(exc.detail) if exc.detail else "unknown"
        }
    )
