import time
from collections import defaultdict

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from .config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiter. Per IP, sliding window 60s."""

    def __init__(self, app):
        super().__init__(app)
        self._hits: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        # Skip health check and static files
        if request.url.path in ("/health", "/"):
            return await call_next(request)

        ip = request.headers.get("cf-connecting-ip") or request.client.host
        now = time.monotonic()
        window = 60.0

        # Clean old entries
        hits = self._hits[ip]
        self._hits[ip] = [t for t in hits if now - t < window]
        hits = self._hits[ip]

        # Determine limit (auth gets more)
        auth = request.headers.get("authorization", "")
        limit = settings.rate_limit_auth if auth.startswith("Bearer ") else settings.rate_limit_anon

        remaining = max(0, limit - len(hits))

        if len(hits) >= limit:
            return Response(
                content='{"detail":"Rate limit exceeded. Try again later."}',
                status_code=429,
                media_type="application/json",
                headers={
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "Retry-After": "60",
                },
            )

        hits.append(now)

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
