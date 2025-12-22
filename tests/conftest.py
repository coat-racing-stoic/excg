"""
Pytest configuration and fixtures for FixedFloatApi-Python tests
"""
import pytest
import asyncio
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any, List

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport


# Test API credentials
TEST_API_KEY = "test_api_key_12345678"
TEST_API_SECRET = "test_api_secret_12345678"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_settings():
    """Mock settings for tests"""
    with patch('config.settings') as mock:
        mock.fixedfloat_api_key = TEST_API_KEY
        mock.fixedfloat_api_secret = TEST_API_SECRET
        mock.redis_url = "redis://localhost:6379"
        mock.rates_cache_enabled = True
        mock.rates_update_interval = 20
        mock.rates_cache_ttl = 60
        mock.rate_limit_requests_per_minute = 100
        mock.rate_limit_default_weight = 1
        mock.rate_limit_create_order_weight = 5
        mock.log_api_requests = True
        mock.log_api_responses = True
        mock.log_request_data = True
        mock.log_response_data = True
        mock.debug = True
        yield mock


@pytest.fixture
def mock_redis():
    """Mock Redis client for tests"""
    mock = AsyncMock()
    mock.ping = AsyncMock(return_value=True)
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=True)
    mock.close = AsyncMock()
    return mock


@pytest.fixture
def sample_fixed_rates() -> List[Dict[str, Any]]:
    """Sample fixed rates data"""
    return [
        {
            "from": "BTC",
            "to": "ETH",
            "in": 1.0,
            "out": 29.5,
            "amount": 590.0,
            "tofee": "0.0001 ETH",
            "minamount": "0.0001 BTC",
            "maxamount": "10.0 BTC"
        },
        {
            "from": "ETH",
            "to": "USDT",
            "in": 1.0,
            "out": 3000.0,
            "amount": 1500000.0,
            "tofee": None,
            "minamount": "0.01 ETH",
            "maxamount": "100.0 ETH"
        },
        {
            "from": "BTC",
            "to": "USDT",
            "in": 1.0,
            "out": 88500.0,
            "amount": 4425000.0,
            "tofee": "0.5 USDT",
            "minamount": "0.0001 BTC",
            "maxamount": "5.0 BTC"
        }
    ]


@pytest.fixture
def sample_float_rates() -> List[Dict[str, Any]]:
    """Sample float rates data"""
    return [
        {
            "from": "BTC",
            "to": "ETH",
            "in": 1.0,
            "out": 29.8,
            "amount": 596.0,
            "tofee": None,
            "minamount": "0.0001 BTC",
            "maxamount": "15.0 BTC"
        },
        {
            "from": "ETH",
            "to": "USDT",
            "in": 1.0,
            "out": 3010.0,
            "amount": 1505000.0,
            "tofee": None,
            "minamount": "0.01 ETH",
            "maxamount": "150.0 ETH"
        }
    ]


@pytest.fixture
def sample_currencies() -> List[Dict[str, Any]]:
    """Sample currencies data"""
    return [
        {
            "code": "BTC",
            "coin": "BTC",
            "network": "BTC",
            "name": "Bitcoin",
            "recv": True,
            "send": True,
            "tag": None,
            "logo": "https://example.com/btc.png",
            "color": "#F7931A",
            "priority": 100
        },
        {
            "code": "ETH",
            "coin": "ETH",
            "network": "ETH",
            "name": "Ethereum",
            "recv": True,
            "send": True,
            "tag": None,
            "logo": "https://example.com/eth.png",
            "color": "#627EEA",
            "priority": 90
        },
        {
            "code": "USDT",
            "coin": "USDT",
            "network": "ETH",
            "name": "Tether USD",
            "recv": True,
            "send": True,
            "tag": None,
            "logo": "https://example.com/usdt.png",
            "color": "#26A17B",
            "priority": 80
        }
    ]


@pytest.fixture
def sample_order_data() -> Dict[str, Any]:
    """Sample order data"""
    return {
        "id": "ORDER123",
        "type": "fixed",
        "email": "test@example.com",
        "status": "new",
        "token": "token123",
        "time": {
            "reg": 1703289600,
            "start": None,
            "finish": None,
            "update": 1703289600,
            "expiration": 1703293200,
            "left": 3600
        },
        "from": {
            "code": "BTC",
            "coin": "BTC",
            "network": "BTC",
            "name": "Bitcoin",
            "alias": "Bitcoin",
            "amount": "0.1",
            "address": "bc1qtest123",
            "addressAlt": None,
            "tag": None,
            "tagName": None,
            "reqConfirmations": 2,
            "maxConfirmations": 6,
            "tx": {
                "id": None,
                "amount": None,
                "fee": None,
                "ccyfee": None,
                "timeReg": None,
                "timeBlock": None,
                "confirmations": None
            }
        },
        "to": {
            "code": "ETH",
            "coin": "ETH",
            "network": "ETH",
            "name": "Ethereum",
            "alias": "Ethereum",
            "amount": "2.95",
            "address": "0xtest123",
            "addressAlt": None,
            "tag": None,
            "tagName": None,
            "reqConfirmations": 12,
            "maxConfirmations": 30,
            "tx": {
                "id": None,
                "amount": None,
                "fee": None,
                "ccyfee": None,
                "timeReg": None,
                "timeBlock": None,
                "confirmations": None
            }
        },
        "back": None,
        "emergency": {
            "status": [],
            "choice": "",
            "repeat": ""
        }
    }


@pytest.fixture
def mock_fixedfloat_api(sample_currencies, sample_fixed_rates, sample_order_data):
    """Mock FixedFloat API"""
    mock = MagicMock()
    mock.ccies = MagicMock(return_value=sample_currencies)
    mock.price = MagicMock(return_value={
        "from": {
            "code": "BTC",
            "network": "BTC",
            "coin": "BTC",
            "amount": "0.1",
            "rate": "1",
            "precision": 8,
            "min": "0.0001",
            "max": "10",
            "usd": "8850",
            "btc": "0.1"
        },
        "to": {
            "code": "ETH",
            "network": "ETH",
            "coin": "ETH",
            "amount": "2.95",
            "rate": "29.5",
            "precision": 8,
            "min": "0.01",
            "max": "100",
            "usd": "8850",
            "btc": "0.1"
        },
        "errors": []
    })
    mock.create = MagicMock(return_value=sample_order_data)
    mock.order = MagicMock(return_value=sample_order_data)
    mock.emergency = MagicMock(return_value={"status": "processed", "message": "OK"})
    mock.setEmail = MagicMock(return_value={"status": "email_set"})
    mock.qr = MagicMock(return_value=[
        {"title": "Address", "src": "data:image/png;base64,test", "checked": True}
    ])
    mock.get_rates_fixed_xml = MagicMock(return_value=sample_fixed_rates)
    mock.get_rates_float_xml = MagicMock(return_value=sample_fixed_rates)
    return mock


@pytest.fixture
def auth_headers():
    """Generate valid auth headers for testing"""
    import hmac
    import hashlib
    
    def generate_headers(body: str = "") -> Dict[str, str]:
        signature = hmac.new(
            TEST_API_SECRET.encode('utf-8'),
            body.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return {
            "X-API-KEY": TEST_API_KEY,
            "X-API-SIGN": signature,
            "Content-Type": "application/json"
        }
    
    return generate_headers


@pytest.fixture
def invalid_auth_headers():
    """Generate invalid auth headers for testing"""
    return {
        "X-API-KEY": "invalid_key",
        "X-API-SIGN": "invalid_signature",
        "Content-Type": "application/json"
    }


@pytest.fixture
async def test_app():
    """Create test FastAPI application"""
    # Import here to avoid circular imports
    with patch.dict(os.environ, {
        'FIXEDFLOAT_API_KEY': TEST_API_KEY,
        'FIXEDFLOAT_API_SECRET': TEST_API_SECRET,
        'REDIS_URL': 'redis://localhost:6379',
        'RATES_CACHE_ENABLED': 'false'  # Disable cache for most tests
    }):
        from main import app
        yield app


@pytest.fixture
async def async_client(test_app):
    """Create async HTTP client for testing"""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def sync_client(test_app):
    """Create sync HTTP client for testing"""
    with TestClient(test_app) as client:
        yield client


# Helper functions for tests
def create_signature(api_secret: str, data: str) -> str:
    """Create HMAC-SHA256 signature"""
    import hmac
    import hashlib
    return hmac.new(
        api_secret.encode('utf-8'),
        data.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()


def assert_api_response(response, expected_code: int = 0):
    """Assert standard API response format"""
    assert response.status_code == 200
    data = response.json()
    assert "code" in data
    assert "msg" in data
    assert data["code"] == expected_code
