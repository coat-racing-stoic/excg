"""
Tests for rate_limiter.py - Rate limiting module
"""
import pytest
import time
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestRateLimiter:
    """Tests for RateLimiter class"""
    
    def test_init(self):
        """Test RateLimiter initialization"""
        with patch('rate_limiter.settings') as mock_settings:
            mock_settings.rate_limit_requests_per_minute = 100
            mock_settings.rate_limit_default_weight = 1
            mock_settings.rate_limit_create_order_weight = 5
            
            from rate_limiter import RateLimiter
            limiter = RateLimiter()
            
            assert limiter.window_size == 60
            assert limiter.max_weight == 100
            assert limiter.requests == {}
    
    def test_get_current_window(self):
        """Test _get_current_window method"""
        with patch('rate_limiter.settings') as mock_settings:
            mock_settings.rate_limit_requests_per_minute = 100
            
            from rate_limiter import RateLimiter
            limiter = RateLimiter()
            
            current_time = time.time()
            expected_window = int(current_time // 60)
            
            result = limiter._get_current_window()
            
            # Allow for small time difference
            assert abs(result - expected_window) <= 1
    
    def test_get_current_usage_new_key(self):
        """Test get_current_usage for new API key"""
        with patch('rate_limiter.settings') as mock_settings:
            mock_settings.rate_limit_requests_per_minute = 100
            
            from rate_limiter import RateLimiter
            limiter = RateLimiter()
            
            usage = limiter.get_current_usage("new_api_key")
            
            assert usage["used_weight"] == 0
            assert usage["remaining"] == 100
    
    def test_get_current_usage_existing_key(self):
        """Test get_current_usage for existing API key with usage"""
        with patch('rate_limiter.settings') as mock_settings:
            mock_settings.rate_limit_requests_per_minute = 100
            
            from rate_limiter import RateLimiter
            limiter = RateLimiter()
            
            # Add some usage
            limiter.check_rate_limit("test_key", weight=30)
            
            usage = limiter.get_current_usage("test_key")
            
            assert usage["used_weight"] == 30
            assert usage["remaining"] == 70
    
    def test_check_rate_limit_within_limit(self):
        """Test check_rate_limit when within limits"""
        with patch('rate_limiter.settings') as mock_settings:
            mock_settings.rate_limit_requests_per_minute = 100
            
            from rate_limiter import RateLimiter
            limiter = RateLimiter()
            
            result = limiter.check_rate_limit("test_key", weight=10)
            
            assert result is True
    
    def test_check_rate_limit_exceeds_limit(self):
        """Test check_rate_limit when exceeding limits"""
        with patch('rate_limiter.settings') as mock_settings:
            mock_settings.rate_limit_requests_per_minute = 100
            
            from rate_limiter import RateLimiter
            limiter = RateLimiter()
            
            # Use up the limit
            limiter.check_rate_limit("test_key", weight=100)
            
            # Try to exceed
            result = limiter.check_rate_limit("test_key", weight=1)
            
            assert result is False
    
    def test_check_rate_limit_accumulates(self):
        """Test that rate limit accumulates correctly"""
        with patch('rate_limiter.settings') as mock_settings:
            mock_settings.rate_limit_requests_per_minute = 100
            
            from rate_limiter import RateLimiter
            limiter = RateLimiter()
            
            # Make multiple requests
            limiter.check_rate_limit("test_key", weight=20)
            limiter.check_rate_limit("test_key", weight=30)
            limiter.check_rate_limit("test_key", weight=40)
            
            usage = limiter.get_current_usage("test_key")
            
            assert usage["used_weight"] == 90
            assert usage["remaining"] == 10
    
    def test_get_endpoint_weight_known_endpoint(self):
        """Test get_endpoint_weight for known endpoint"""
        with patch('rate_limiter.settings') as mock_settings:
            mock_settings.rate_limit_requests_per_minute = 100
            mock_settings.rate_limit_default_weight = 1
            mock_settings.rate_limit_create_order_weight = 5
            
            from rate_limiter import RateLimiter
            limiter = RateLimiter()
            
            weight = limiter.get_endpoint_weight("/api/v2/create", "POST")
            
            assert weight == 5
    
    def test_get_endpoint_weight_unknown_endpoint(self):
        """Test get_endpoint_weight for unknown endpoint"""
        with patch('rate_limiter.settings') as mock_settings:
            mock_settings.rate_limit_requests_per_minute = 100
            mock_settings.rate_limit_default_weight = 1
            mock_settings.rate_limit_create_order_weight = 5
            
            from rate_limiter import RateLimiter
            limiter = RateLimiter()
            
            weight = limiter.get_endpoint_weight("/api/v2/unknown", "POST")
            
            assert weight == 1
    
    def test_reset_usage(self):
        """Test reset_usage method"""
        with patch('rate_limiter.settings') as mock_settings:
            mock_settings.rate_limit_requests_per_minute = 100
            
            from rate_limiter import RateLimiter
            limiter = RateLimiter()
            
            # Add some usage
            limiter.check_rate_limit("test_key", weight=50)
            
            # Reset
            result = limiter.reset_usage("test_key")
            
            assert result is True
            
            # Check usage is reset
            usage = limiter.get_current_usage("test_key")
            assert usage["used_weight"] == 0
    
    def test_reset_usage_nonexistent_key(self):
        """Test reset_usage for non-existent key"""
        with patch('rate_limiter.settings') as mock_settings:
            mock_settings.rate_limit_requests_per_minute = 100
            
            from rate_limiter import RateLimiter
            limiter = RateLimiter()
            
            result = limiter.reset_usage("nonexistent_key")
            
            assert result is False
    
    def test_get_all_usage(self):
        """Test get_all_usage method"""
        with patch('rate_limiter.settings') as mock_settings:
            mock_settings.rate_limit_requests_per_minute = 100
            
            from rate_limiter import RateLimiter
            limiter = RateLimiter()
            
            # Add usage for multiple keys
            limiter.check_rate_limit("key1_12345678", weight=10)
            limiter.check_rate_limit("key2_12345678", weight=20)
            
            all_usage = limiter.get_all_usage()
            
            assert len(all_usage) == 2
            # Keys should be truncated
            assert "key1_123..." in all_usage
            assert "key2_123..." in all_usage
    
    def test_cleanup_old_windows(self):
        """Test _cleanup_old_windows method"""
        with patch('rate_limiter.settings') as mock_settings:
            mock_settings.rate_limit_requests_per_minute = 100
            
            from rate_limiter import RateLimiter
            limiter = RateLimiter()
            
            # Manually add old window data
            current_window = limiter._get_current_window()
            old_window = current_window - 2
            
            limiter.requests["test_key"] = {
                old_window: 50,
                current_window: 30
            }
            
            # Cleanup should remove old window
            limiter._cleanup_old_windows("test_key", current_window)
            
            assert old_window not in limiter.requests["test_key"]
            assert current_window in limiter.requests["test_key"]


class TestCheckRateLimitMiddleware:
    """Tests for check_rate_limit_middleware function"""
    
    @pytest.mark.asyncio
    async def test_middleware_skips_xml_endpoints(self):
        """Test that middleware skips XML endpoints"""
        with patch('rate_limiter.settings') as mock_settings:
            mock_settings.rate_limit_requests_per_minute = 100
            mock_settings.rate_limit_default_weight = 1
            mock_settings.rate_limit_create_order_weight = 5
            
            from rate_limiter import check_rate_limit_middleware
            
            mock_request = MagicMock()
            mock_request.url.path = "/rates/fixed.xml"
            mock_request.method = "GET"
            
            # Should not raise
            await check_rate_limit_middleware(mock_request, "test_key")
    
    @pytest.mark.asyncio
    async def test_middleware_allows_within_limit(self):
        """Test that middleware allows requests within limit"""
        with patch('rate_limiter.settings') as mock_settings:
            mock_settings.rate_limit_requests_per_minute = 100
            mock_settings.rate_limit_default_weight = 1
            mock_settings.rate_limit_create_order_weight = 5
            
            # Reset rate limiter
            import rate_limiter
            rate_limiter.rate_limiter = rate_limiter.RateLimiter()
            
            from rate_limiter import check_rate_limit_middleware
            
            mock_request = MagicMock()
            mock_request.url.path = "/api/v2/ccies"
            mock_request.method = "POST"
            
            # Should not raise
            await check_rate_limit_middleware(mock_request, "test_key_middleware")
    
    @pytest.mark.asyncio
    async def test_middleware_blocks_exceeding_limit(self):
        """Test that middleware blocks requests exceeding limit"""
        with patch('rate_limiter.settings') as mock_settings:
            mock_settings.rate_limit_requests_per_minute = 10
            mock_settings.rate_limit_default_weight = 1
            mock_settings.rate_limit_create_order_weight = 5
            
            # Reset rate limiter with low limit
            import rate_limiter
            rate_limiter.rate_limiter = rate_limiter.RateLimiter()
            
            from rate_limiter import check_rate_limit_middleware
            
            mock_request = MagicMock()
            mock_request.url.path = "/api/v2/ccies"
            mock_request.method = "POST"
            
            # Use up the limit
            for _ in range(10):
                await check_rate_limit_middleware(mock_request, "test_key_block")
            
            # Next request should be blocked
            with pytest.raises(HTTPException) as exc_info:
                await check_rate_limit_middleware(mock_request, "test_key_block")
            
            assert exc_info.value.status_code == 429
            assert "Rate limit exceeded" in str(exc_info.value.detail)


class TestGetRateLimitHeaders:
    """Tests for get_rate_limit_headers function"""
    
    def test_get_rate_limit_headers(self):
        """Test get_rate_limit_headers function"""
        with patch('rate_limiter.settings') as mock_settings:
            mock_settings.rate_limit_requests_per_minute = 100
            mock_settings.rate_limit_default_weight = 1
            mock_settings.rate_limit_create_order_weight = 5
            
            # Reset rate limiter
            import rate_limiter
            rate_limiter.rate_limiter = rate_limiter.RateLimiter()
            
            from rate_limiter import get_rate_limit_headers
            
            # Add some usage
            rate_limiter.rate_limiter.check_rate_limit("test_key_headers", weight=30)
            
            headers = get_rate_limit_headers("test_key_headers")
            
            assert "X-RateLimit-Limit" in headers
            assert "X-RateLimit-Remaining" in headers
            assert "X-RateLimit-Reset" in headers
            assert headers["X-RateLimit-Limit"] == "100"
            assert headers["X-RateLimit-Remaining"] == "70"
