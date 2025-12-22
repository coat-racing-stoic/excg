"""
Tests for API endpoints in main.py
"""
import pytest
import json
import hmac
import hashlib
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Test credentials
TEST_API_KEY = "test_api_key_12345678"
TEST_API_SECRET = "test_api_secret_12345678"


def create_signature(data: str) -> str:
    """Create HMAC-SHA256 signature"""
    return hmac.new(
        TEST_API_SECRET.encode('utf-8'),
        data.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()


class TestHealthEndpoint:
    """Tests for /health endpoint"""
    
    def test_health_check(self):
        """Test health check endpoint"""
        with patch.dict(os.environ, {
            'FIXEDFLOAT_API_KEY': TEST_API_KEY,
            'FIXEDFLOAT_API_SECRET': TEST_API_SECRET,
            'RATES_CACHE_ENABLED': 'false'
        }):
            # Need to reload modules with new env vars
            from main import app
            client = TestClient(app)
            
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "timestamp" in data
            assert "version" in data


class TestCacheEndpoints:
    """Tests for cache management endpoints"""
    
    @pytest.fixture
    def mock_rates_cache(self):
        """Mock rates cache"""
        mock = AsyncMock()
        mock.is_connected = AsyncMock(return_value=True)
        mock.get_cache_status = AsyncMock(return_value={
            "connected": True,
            "fixed_rates": {"count": 100, "cached": True},
            "float_rates": {"count": 100, "cached": True}
        })
        return mock
    
    def test_cache_status(self, mock_rates_cache):
        """Test cache status endpoint"""
        with patch.dict(os.environ, {
            'FIXEDFLOAT_API_KEY': TEST_API_KEY,
            'FIXEDFLOAT_API_SECRET': TEST_API_SECRET,
            'RATES_CACHE_ENABLED': 'true'
        }):
            with patch('main.rates_cache', mock_rates_cache):
                with patch('main.rates_updater') as mock_updater:
                    mock_updater.is_running = True
                    mock_updater.update_interval = 20
                    mock_updater.consecutive_errors = 0
                    mock_updater.max_consecutive_errors = 5
                    
                    from main import app
                    client = TestClient(app)
                    
                    response = client.get("/api/cache/status")
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert "enabled" in data
                    assert "cache" in data


class TestRatesEndpoints:
    """Tests for rates endpoints"""
    
    @pytest.fixture
    def sample_rates(self):
        """Sample rates data"""
        return [
            {"from": "BTC", "to": "ETH", "in": 1.0, "out": 29.5, "amount": 590.0},
            {"from": "ETH", "to": "USDT", "in": 1.0, "out": 3000.0, "amount": 1500000.0}
        ]
    
    def test_get_fixed_rates(self, sample_rates):
        """Test get fixed rates endpoint"""
        with patch.dict(os.environ, {
            'FIXEDFLOAT_API_KEY': TEST_API_KEY,
            'FIXEDFLOAT_API_SECRET': TEST_API_SECRET,
            'RATES_CACHE_ENABLED': 'true'
        }):
            mock_cache = AsyncMock()
            mock_cache.get_fixed_rates = AsyncMock(return_value=sample_rates)
            
            with patch('main.rates_cache', mock_cache):
                from main import app
                client = TestClient(app)
                
                response = client.get("/api/rates/fixed")
                
                assert response.status_code == 200
                data = response.json()
                assert isinstance(data, list)
    
    def test_get_float_rates(self, sample_rates):
        """Test get float rates endpoint"""
        with patch.dict(os.environ, {
            'FIXEDFLOAT_API_KEY': TEST_API_KEY,
            'FIXEDFLOAT_API_SECRET': TEST_API_SECRET,
            'RATES_CACHE_ENABLED': 'true'
        }):
            mock_cache = AsyncMock()
            mock_cache.get_float_rates = AsyncMock(return_value=sample_rates)
            
            with patch('main.rates_cache', mock_cache):
                from main import app
                client = TestClient(app)
                
                response = client.get("/api/rates/float")
                
                assert response.status_code == 200
                data = response.json()
                assert isinstance(data, list)
    
    def test_get_rate_for_pair(self, sample_rates):
        """Test get rate for specific pair endpoint"""
        with patch.dict(os.environ, {
            'FIXEDFLOAT_API_KEY': TEST_API_KEY,
            'FIXEDFLOAT_API_SECRET': TEST_API_SECRET,
            'RATES_CACHE_ENABLED': 'true'
        }):
            mock_cache = AsyncMock()
            mock_cache.get_rate_for_pair = AsyncMock(return_value=sample_rates[0])
            
            with patch('main.rates_cache', mock_cache):
                from main import app
                client = TestClient(app)
                
                response = client.get("/api/rates/pair/BTC/ETH?rate_type=fixed")
                
                assert response.status_code == 200
                data = response.json()
                assert data["code"] == 0
                assert "data" in data
    
    def test_get_rate_for_pair_not_found(self):
        """Test get rate for pair when not found"""
        with patch.dict(os.environ, {
            'FIXEDFLOAT_API_KEY': TEST_API_KEY,
            'FIXEDFLOAT_API_SECRET': TEST_API_SECRET,
            'RATES_CACHE_ENABLED': 'true'
        }):
            mock_cache = AsyncMock()
            mock_cache.get_rate_for_pair = AsyncMock(return_value=None)
            
            with patch('main.rates_cache', mock_cache):
                from main import app
                client = TestClient(app)
                
                response = client.get("/api/rates/pair/XRP/DOGE?rate_type=fixed")
                
                assert response.status_code == 200
                data = response.json()
                assert data["code"] == 404


class TestXMLEndpoints:
    """Tests for XML rate endpoints"""
    
    @pytest.fixture
    def mock_service(self):
        """Mock FixedFloat service"""
        mock = MagicMock()
        mock.get_fixed_rates_xml = AsyncMock(return_value=[
            MagicMock(
                **{"from": "BTC", "to": "ETH", "in": 1.0, "out": 29.5}
            )
        ])
        mock.get_float_rates_xml = AsyncMock(return_value=[
            MagicMock(
                **{"from": "BTC", "to": "ETH", "in": 1.0, "out": 29.8}
            )
        ])
        return mock
    
    def test_fixed_rates_xml(self, mock_service):
        """Test fixed rates XML endpoint"""
        with patch.dict(os.environ, {
            'FIXEDFLOAT_API_KEY': TEST_API_KEY,
            'FIXEDFLOAT_API_SECRET': TEST_API_SECRET,
            'RATES_CACHE_ENABLED': 'false'
        }):
            with patch('main.fixedfloat_service', mock_service):
                from main import app
                client = TestClient(app)
                
                response = client.get("/rates/fixed.xml")
                
                assert response.status_code == 200
                assert "xml" in response.headers.get("content-type", "").lower()
    
    def test_float_rates_xml(self, mock_service):
        """Test float rates XML endpoint"""
        with patch.dict(os.environ, {
            'FIXEDFLOAT_API_KEY': TEST_API_KEY,
            'FIXEDFLOAT_API_SECRET': TEST_API_SECRET,
            'RATES_CACHE_ENABLED': 'false'
        }):
            with patch('main.fixedfloat_service', mock_service):
                from main import app
                client = TestClient(app)
                
                response = client.get("/rates/float.xml")
                
                assert response.status_code == 200
                assert "xml" in response.headers.get("content-type", "").lower()


class TestAuthenticatedEndpoints:
    """Tests for authenticated API endpoints"""
    
    def test_ccies_without_auth(self):
        """Test currencies endpoint without authentication"""
        with patch.dict(os.environ, {
            'FIXEDFLOAT_API_KEY': TEST_API_KEY,
            'FIXEDFLOAT_API_SECRET': TEST_API_SECRET,
            'RATES_CACHE_ENABLED': 'false'
        }):
            from main import app
            client = TestClient(app)
            
            response = client.post("/api/v2/ccies")
            
            assert response.status_code == 401
            data = response.json()
            assert "Missing X-API-KEY or X-API-SIGN headers" in str(data)
    
    def test_ccies_with_invalid_auth(self):
        """Test currencies endpoint with invalid authentication"""
        with patch.dict(os.environ, {
            'FIXEDFLOAT_API_KEY': TEST_API_KEY,
            'FIXEDFLOAT_API_SECRET': TEST_API_SECRET,
            'RATES_CACHE_ENABLED': 'false'
        }):
            from main import app
            client = TestClient(app)
            
            headers = {
                "X-API-KEY": "invalid_key",
                "X-API-SIGN": "invalid_signature"
            }
            
            response = client.post("/api/v2/ccies", headers=headers)
            
            assert response.status_code == 401
    
    def test_price_without_auth(self):
        """Test price endpoint without authentication"""
        with patch.dict(os.environ, {
            'FIXEDFLOAT_API_KEY': TEST_API_KEY,
            'FIXEDFLOAT_API_SECRET': TEST_API_SECRET,
            'RATES_CACHE_ENABLED': 'false'
        }):
            from main import app
            client = TestClient(app)
            
            response = client.post("/api/v2/price", json={
                "fromCcy": "BTC",
                "toCcy": "ETH",
                "amount": 1,
                "direction": "from",
                "type": "fixed"
            })
            
            assert response.status_code == 401


class TestErrorHandling:
    """Tests for error handling"""
    
    def test_404_not_found(self):
        """Test 404 for non-existent endpoint"""
        with patch.dict(os.environ, {
            'FIXEDFLOAT_API_KEY': TEST_API_KEY,
            'FIXEDFLOAT_API_SECRET': TEST_API_SECRET,
            'RATES_CACHE_ENABLED': 'false'
        }):
            from main import app
            client = TestClient(app)
            
            response = client.get("/nonexistent/endpoint")
            
            assert response.status_code == 404
    
    def test_method_not_allowed(self):
        """Test 405 for wrong HTTP method"""
        with patch.dict(os.environ, {
            'FIXEDFLOAT_API_KEY': TEST_API_KEY,
            'FIXEDFLOAT_API_SECRET': TEST_API_SECRET,
            'RATES_CACHE_ENABLED': 'false'
        }):
            from main import app
            client = TestClient(app)
            
            # /api/v2/ccies expects POST, not GET
            response = client.get("/api/v2/ccies")
            
            assert response.status_code == 405


class TestResponseHeaders:
    """Tests for response headers"""
    
    def test_request_id_header(self):
        """Test X-Request-ID header is present"""
        with patch.dict(os.environ, {
            'FIXEDFLOAT_API_KEY': TEST_API_KEY,
            'FIXEDFLOAT_API_SECRET': TEST_API_SECRET,
            'RATES_CACHE_ENABLED': 'false'
        }):
            from main import app
            client = TestClient(app)
            
            response = client.get("/health")
            
            assert "X-Request-ID" in response.headers
    
    def test_process_time_header(self):
        """Test X-Process-Time header is present"""
        with patch.dict(os.environ, {
            'FIXEDFLOAT_API_KEY': TEST_API_KEY,
            'FIXEDFLOAT_API_SECRET': TEST_API_SECRET,
            'RATES_CACHE_ENABLED': 'false'
        }):
            from main import app
            client = TestClient(app)
            
            response = client.get("/health")
            
            assert "X-Process-Time" in response.headers
