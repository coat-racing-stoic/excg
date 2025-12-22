"""
Tests for redis_cache.py - Redis caching module
"""
import pytest
import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestRatesCache:
    """Tests for RatesCache class"""
    
    @pytest.fixture
    def mock_redis_client(self):
        """Create mock Redis client"""
        mock = AsyncMock()
        mock.ping = AsyncMock(return_value=True)
        mock.get = AsyncMock(return_value=None)
        mock.set = AsyncMock(return_value=True)
        mock.delete = AsyncMock(return_value=True)
        mock.close = AsyncMock()
        return mock
    
    @pytest.fixture
    def sample_rates(self):
        """Sample rates data"""
        return [
            {"from": "BTC", "to": "ETH", "in": 1.0, "out": 29.5, "amount": 590.0},
            {"from": "ETH", "to": "USDT", "in": 1.0, "out": 3000.0, "amount": 1500000.0}
        ]
    
    def test_init(self):
        """Test RatesCache initialization"""
        with patch('redis_cache.settings') as mock_settings:
            mock_settings.redis_url = "redis://localhost:6379"
            mock_settings.rates_cache_ttl = 60
            
            from redis_cache import RatesCache
            cache = RatesCache()
            
            assert cache.redis_url == "redis://localhost:6379"
            assert cache.ttl == 60
            assert cache._redis is None
    
    @pytest.mark.asyncio
    async def test_connect_success(self, mock_redis_client):
        """Test successful Redis connection"""
        with patch('redis_cache.settings') as mock_settings:
            mock_settings.redis_url = "redis://localhost:6379"
            mock_settings.rates_cache_ttl = 60
            
            with patch('redis_cache.aioredis.from_url', return_value=mock_redis_client):
                from redis_cache import RatesCache
                cache = RatesCache()
                
                result = await cache.connect()
                
                assert result is True
                mock_redis_client.ping.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_connect_failure(self):
        """Test Redis connection failure"""
        with patch('redis_cache.settings') as mock_settings:
            mock_settings.redis_url = "redis://localhost:6379"
            mock_settings.rates_cache_ttl = 60
            
            mock_redis = AsyncMock()
            mock_redis.ping = AsyncMock(side_effect=Exception("Connection failed"))
            
            with patch('redis_cache.aioredis.from_url', return_value=mock_redis):
                from redis_cache import RatesCache
                cache = RatesCache()
                
                result = await cache.connect()
                
                assert result is False
    
    @pytest.mark.asyncio
    async def test_disconnect(self, mock_redis_client):
        """Test Redis disconnection"""
        with patch('redis_cache.settings') as mock_settings:
            mock_settings.redis_url = "redis://localhost:6379"
            mock_settings.rates_cache_ttl = 60
            
            from redis_cache import RatesCache
            cache = RatesCache()
            cache._redis = mock_redis_client
            
            await cache.disconnect()
            
            mock_redis_client.close.assert_called_once()
            assert cache._redis is None
    
    @pytest.mark.asyncio
    async def test_set_fixed_rates(self, mock_redis_client, sample_rates):
        """Test setting fixed rates in cache"""
        with patch('redis_cache.settings') as mock_settings:
            mock_settings.redis_url = "redis://localhost:6379"
            mock_settings.rates_cache_ttl = 60
            
            from redis_cache import RatesCache
            cache = RatesCache()
            cache._redis = mock_redis_client
            
            result = await cache.set_fixed_rates(sample_rates)
            
            assert result is True
            mock_redis_client.set.assert_called()
    
    @pytest.mark.asyncio
    async def test_set_float_rates(self, mock_redis_client, sample_rates):
        """Test setting float rates in cache"""
        with patch('redis_cache.settings') as mock_settings:
            mock_settings.redis_url = "redis://localhost:6379"
            mock_settings.rates_cache_ttl = 60
            
            from redis_cache import RatesCache
            cache = RatesCache()
            cache._redis = mock_redis_client
            
            result = await cache.set_float_rates(sample_rates)
            
            assert result is True
            mock_redis_client.set.assert_called()
    
    @pytest.mark.asyncio
    async def test_get_fixed_rates_cache_hit(self, mock_redis_client, sample_rates):
        """Test getting fixed rates from cache (cache hit)"""
        with patch('redis_cache.settings') as mock_settings:
            mock_settings.redis_url = "redis://localhost:6379"
            mock_settings.rates_cache_ttl = 60
            
            # Setup mock to return cached data
            cache_data = {
                "rates": sample_rates,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            mock_redis_client.get = AsyncMock(return_value=json.dumps(cache_data))
            
            from redis_cache import RatesCache
            cache = RatesCache()
            cache._redis = mock_redis_client
            
            result = await cache.get_fixed_rates()
            
            assert result is not None
            assert len(result) == 2
    
    @pytest.mark.asyncio
    async def test_get_fixed_rates_cache_miss(self, mock_redis_client):
        """Test getting fixed rates from cache (cache miss)"""
        with patch('redis_cache.settings') as mock_settings:
            mock_settings.redis_url = "redis://localhost:6379"
            mock_settings.rates_cache_ttl = 60
            
            mock_redis_client.get = AsyncMock(return_value=None)
            
            from redis_cache import RatesCache
            cache = RatesCache()
            cache._redis = mock_redis_client
            
            result = await cache.get_fixed_rates()
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_get_float_rates_cache_hit(self, mock_redis_client, sample_rates):
        """Test getting float rates from cache (cache hit)"""
        with patch('redis_cache.settings') as mock_settings:
            mock_settings.redis_url = "redis://localhost:6379"
            mock_settings.rates_cache_ttl = 60
            
            # Setup mock to return cached data
            cache_data = {
                "rates": sample_rates,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            mock_redis_client.get = AsyncMock(return_value=json.dumps(cache_data))
            
            from redis_cache import RatesCache
            cache = RatesCache()
            cache._redis = mock_redis_client
            
            result = await cache.get_float_rates()
            
            assert result is not None
            assert len(result) == 2
    
    @pytest.mark.asyncio
    async def test_get_rate_for_pair_found(self, mock_redis_client, sample_rates):
        """Test getting rate for specific pair (found)"""
        with patch('redis_cache.settings') as mock_settings:
            mock_settings.redis_url = "redis://localhost:6379"
            mock_settings.rates_cache_ttl = 60
            
            # Setup mock to return cached data
            cache_data = {
                "rates": sample_rates,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            mock_redis_client.get = AsyncMock(return_value=json.dumps(cache_data))
            
            from redis_cache import RatesCache
            cache = RatesCache()
            cache._redis = mock_redis_client
            
            result = await cache.get_rate_for_pair("BTC", "ETH", "fixed")
            
            assert result is not None
            assert result["from"] == "BTC"
            assert result["to"] == "ETH"
    
    @pytest.mark.asyncio
    async def test_get_rate_for_pair_not_found(self, mock_redis_client, sample_rates):
        """Test getting rate for specific pair (not found)"""
        with patch('redis_cache.settings') as mock_settings:
            mock_settings.redis_url = "redis://localhost:6379"
            mock_settings.rates_cache_ttl = 60
            
            # Setup mock to return cached data
            cache_data = {
                "rates": sample_rates,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            mock_redis_client.get = AsyncMock(return_value=json.dumps(cache_data))
            
            from redis_cache import RatesCache
            cache = RatesCache()
            cache._redis = mock_redis_client
            
            result = await cache.get_rate_for_pair("XRP", "DOGE", "fixed")
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_get_cache_status(self, mock_redis_client, sample_rates):
        """Test getting cache status"""
        with patch('redis_cache.settings') as mock_settings:
            mock_settings.redis_url = "redis://localhost:6379"
            mock_settings.rates_cache_ttl = 60
            
            # Setup mock to return cached data
            cache_data = {
                "rates": sample_rates,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            mock_redis_client.get = AsyncMock(return_value=json.dumps(cache_data))
            mock_redis_client.ttl = AsyncMock(return_value=45)
            
            from redis_cache import RatesCache
            cache = RatesCache()
            cache._redis = mock_redis_client
            
            status = await cache.get_cache_status()
            
            assert "connected" in status
            assert "fixed_rates" in status
            assert "float_rates" in status
    
    @pytest.mark.asyncio
    async def test_invalidate_cache(self, mock_redis_client):
        """Test cache invalidation"""
        with patch('redis_cache.settings') as mock_settings:
            mock_settings.redis_url = "redis://localhost:6379"
            mock_settings.rates_cache_ttl = 60
            
            from redis_cache import RatesCache
            cache = RatesCache()
            cache._redis = mock_redis_client
            
            result = await cache.invalidate()
            
            assert result is True
            assert mock_redis_client.delete.call_count == 2
    
    @pytest.mark.asyncio
    async def test_is_connected_true(self, mock_redis_client):
        """Test is_connected when connected"""
        with patch('redis_cache.settings') as mock_settings:
            mock_settings.redis_url = "redis://localhost:6379"
            mock_settings.rates_cache_ttl = 60
            
            from redis_cache import RatesCache
            cache = RatesCache()
            cache._redis = mock_redis_client
            
            result = await cache.is_connected()
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_is_connected_false(self):
        """Test is_connected when not connected"""
        with patch('redis_cache.settings') as mock_settings:
            mock_settings.redis_url = "redis://localhost:6379"
            mock_settings.rates_cache_ttl = 60
            
            from redis_cache import RatesCache
            cache = RatesCache()
            
            result = await cache.is_connected()
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_set_rates_no_connection(self, sample_rates):
        """Test setting rates when not connected"""
        with patch('redis_cache.settings') as mock_settings:
            mock_settings.redis_url = "redis://localhost:6379"
            mock_settings.rates_cache_ttl = 60
            
            from redis_cache import RatesCache
            cache = RatesCache()
            # Don't set _redis, simulating no connection
            
            result = await cache.set_fixed_rates(sample_rates)
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_get_rates_no_connection(self):
        """Test getting rates when not connected"""
        with patch('redis_cache.settings') as mock_settings:
            mock_settings.redis_url = "redis://localhost:6379"
            mock_settings.rates_cache_ttl = 60
            
            from redis_cache import RatesCache
            cache = RatesCache()
            # Don't set _redis, simulating no connection
            
            result = await cache.get_fixed_rates()
            
            assert result is None


class TestRatesCacheEdgeCases:
    """Edge case tests for RatesCache"""
    
    @pytest.mark.asyncio
    async def test_set_empty_rates(self):
        """Test setting empty rates list"""
        with patch('redis_cache.settings') as mock_settings:
            mock_settings.redis_url = "redis://localhost:6379"
            mock_settings.rates_cache_ttl = 60
            
            mock_redis = AsyncMock()
            mock_redis.set = AsyncMock(return_value=True)
            
            from redis_cache import RatesCache
            cache = RatesCache()
            cache._redis = mock_redis
            
            result = await cache.set_fixed_rates([])
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_get_rates_invalid_json(self):
        """Test getting rates with invalid JSON in cache"""
        with patch('redis_cache.settings') as mock_settings:
            mock_settings.redis_url = "redis://localhost:6379"
            mock_settings.rates_cache_ttl = 60
            
            mock_redis = AsyncMock()
            mock_redis.get = AsyncMock(return_value="invalid json")
            
            from redis_cache import RatesCache
            cache = RatesCache()
            cache._redis = mock_redis
            
            result = await cache.get_fixed_rates()
            
            # Should handle error gracefully
            assert result is None
    
    @pytest.mark.asyncio
    async def test_redis_error_handling(self):
        """Test Redis error handling"""
        with patch('redis_cache.settings') as mock_settings:
            mock_settings.redis_url = "redis://localhost:6379"
            mock_settings.rates_cache_ttl = 60
            
            mock_redis = AsyncMock()
            mock_redis.get = AsyncMock(side_effect=Exception("Redis error"))
            
            from redis_cache import RatesCache
            cache = RatesCache()
            cache._redis = mock_redis
            
            result = await cache.get_fixed_rates()
            
            # Should handle error gracefully
            assert result is None
