"""
Middleware for authentication, rate limiting, and security.
"""

from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable, Dict
import time
from collections import defaultdict
from api.config import (
    API_KEY, REQUIRE_API_KEY, API_KEY_HEADER,
    RATE_LIMIT_ENABLED, RATE_LIMIT_REQUESTS, RATE_LIMIT_WINDOW
)

# Rate limiting storage (in-memory, will be replaced with Redis later)
rate_limit_storage: Dict[str, Dict[str, float]] = defaultdict(lambda: {"count": 0, "reset_time": 0})


class APIKeyMiddleware(BaseHTTPMiddleware):
    """
    Middleware to validate API keys for protected endpoints.
    """
    
    async def dispatch(self, request: Request, call_next: Callable):
        # Skip authentication for health check and docs endpoints
        if request.url.path in ["/health", "/", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # If API key is required and configured
        if REQUIRE_API_KEY and API_KEY:
            # Get API key from header
            api_key = request.headers.get(API_KEY_HEADER) or request.headers.get("Authorization", "").replace("Bearer ", "")
            
            if not api_key or api_key != API_KEY:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or missing API key. Provide API key in X-API-Key header."
                )
        
        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to implement rate limiting per IP address.
    """
    
    async def dispatch(self, request: Request, call_next: Callable):
        # Skip rate limiting for health check and docs
        if request.url.path in ["/health", "/", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        if not RATE_LIMIT_ENABLED:
            return await call_next(request)
        
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Check rate limit
        current_time = time.time()
        client_data = rate_limit_storage[client_ip]
        
        # Reset if window expired
        if current_time > client_data["reset_time"]:
            client_data["count"] = 0
            client_data["reset_time"] = current_time + RATE_LIMIT_WINDOW
        
        # Check if limit exceeded
        if client_data["count"] >= RATE_LIMIT_REQUESTS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Maximum {RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_WINDOW} seconds."
            )
        
        # Increment counter
        client_data["count"] += 1
        
        # Add rate limit headers
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(RATE_LIMIT_REQUESTS)
        response.headers["X-RateLimit-Remaining"] = str(RATE_LIMIT_REQUESTS - client_data["count"])
        response.headers["X-RateLimit-Reset"] = str(int(client_data["reset_time"]))
        
        return response


# Security headers middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses.
    """
    
    async def dispatch(self, request: Request, call_next: Callable):
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


