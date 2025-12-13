import time
import asyncio
from typing import Dict, Optional
from fastapi import HTTPException, Request, status
from config import settings

class RateLimiter:
    """Rate limiter with weighted requests support"""
    
    def __init__(self):
        # In-memory storage for rate limiting (use Redis in production)
        self.requests: Dict[str, Dict[str, any]] = {}
        self.window_size = 60  # 1 minute window
        self.max_weight = settings.rate_limit_requests_per_minute
    
    def _get_current_window(self) -> int:
        """Get current time window"""
        return int(time.time() // self.window_size)
    
    def _cleanup_old_windows(self, api_key: str, current_window: int):
        """Remove old time windows"""
        if api_key in self.requests:
            windows_to_remove = [
                window for window in self.requests[api_key].keys()
                if isinstance(window, int) and window < current_window
            ]
            for window in windows_to_remove:
                del self.requests[api_key][window]
    
    def get_current_usage(self, api_key: str) -> Dict[str, int]:
        """Get current usage for API key"""
        current_window = self._get_current_window()
        
        if api_key not in self.requests:
            return {"used_weight": 0, "remaining": self.max_weight}
        
        self._cleanup_old_windows(api_key, current_window)
        
        current_weight = self.requests[api_key].get(current_window, 0)
        remaining = max(0, self.max_weight - current_weight)
        
        return {
            "used_weight": current_weight,
            "remaining": remaining,
            "reset_time": (current_window + 1) * self.window_size
        }
    
    def check_rate_limit(self, api_key: str, weight: int = 1) -> bool:
        """Check if request is within rate limits"""
        current_window = self._get_current_window()
        
        if api_key not in self.requests:
            self.requests[api_key] = {}
        
        self._cleanup_old_windows(api_key, current_window)
        
        current_weight = self.requests[api_key].get(current_window, 0)
        
        if current_weight + weight > self.max_weight:
            return False
        
        # Update usage
        self.requests[api_key][current_window] = current_weight + weight
        return True
    
    def get_endpoint_weight(self, endpoint: str, method: str) -> int:
        """Get weight for specific endpoint"""
        # Define weights for different endpoints
        weights = {
            "/api/v2/create": settings.rate_limit_create_order_weight,
            "/api/v2/ccies": settings.rate_limit_default_weight,
            "/api/v2/price": settings.rate_limit_default_weight,
            "/api/v2/order": settings.rate_limit_default_weight,
            "/api/v2/emergency": settings.rate_limit_default_weight,
            "/api/v2/setEmail": settings.rate_limit_default_weight,
            "/api/v2/qr": settings.rate_limit_default_weight,
        }
        
        return weights.get(endpoint, settings.rate_limit_default_weight)

# Global rate limiter instance
rate_limiter = RateLimiter()

async def check_rate_limit_middleware(request: Request, api_key: str) -> None:
    """Middleware to check rate limits"""
    endpoint = request.url.path
    method = request.method
    
    # Skip rate limiting for XML endpoints (they are free)
    if endpoint.startswith("/rates/"):
        return
    
    weight = rate_limiter.get_endpoint_weight(endpoint, method)
    
    if not rate_limiter.check_rate_limit(api_key, weight):
        usage = rate_limiter.get_current_usage(api_key)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Rate limit exceeded",
                "used_weight": usage["used_weight"],
                "max_weight": rate_limiter.max_weight,
                "reset_time": usage["reset_time"],
                "retry_after": usage["reset_time"] - int(time.time())
            },
            headers={
                "X-RateLimit-Limit": str(rate_limiter.max_weight),
                "X-RateLimit-Remaining": str(usage["remaining"]),
                "X-RateLimit-Reset": str(usage["reset_time"]),
                "Retry-After": str(usage["reset_time"] - int(time.time()))
            }
        )

def get_rate_limit_headers(api_key: str) -> Dict[str, str]:
    """Get rate limit headers for response"""
    usage = rate_limiter.get_current_usage(api_key)
    return {
        "X-RateLimit-Limit": str(rate_limiter.max_weight),
        "X-RateLimit-Remaining": str(usage["remaining"]),
        "X-RateLimit-Reset": str(usage["reset_time"])
    }