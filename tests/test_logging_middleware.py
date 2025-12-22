"""
Tests for logging_middleware.py - Logging middleware module
"""
import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from starlette.responses import JSONResponse

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestLoggingMiddleware:
    """Tests for LoggingMiddleware class"""
    
    @pytest.fixture
    def app_with_middleware(self):
        """Create FastAPI app with logging middleware"""
        with patch.dict(os.environ, {
            'FIXEDFLOAT_API_KEY': 'test_key',
            'FIXEDFLOAT_API_SECRET': 'test_secret',
            'RATES_CACHE_ENABLED': 'false',
            'LOG_API_REQUESTS': 'true',
            'LOG_API_RESPONSES': 'true',
            'LOG_REQUEST_DATA': 'true',
            'LOG_RESPONSE_DATA': 'false'
        }):
            app = FastAPI()
            
            from logging_middleware import LoggingMiddleware, RequestContextMiddleware
            
            app.add_middleware(LoggingMiddleware)
            app.add_middleware(RequestContextMiddleware)
            
            @app.get("/test")
            async def test_endpoint():
                return {"message": "success"}
            
            @app.post("/test-post")
            async def test_post_endpoint(data: dict = None):
                return {"received": data}
            
            @app.get("/error")
            async def error_endpoint():
                raise ValueError("Test error")
            
            yield app
    
    @pytest.fixture
    def client(self, app_with_middleware):
        """Create test client"""
        return TestClient(app_with_middleware, raise_server_exceptions=False)
    
    def test_adds_request_id_header(self, client):
        """Test that middleware adds X-Request-ID header"""
        response = client.get("/test")
        
        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) > 0
    
    def test_adds_process_time_header(self, client):
        """Test that middleware adds X-Process-Time header"""
        response = client.get("/test")
        
        assert "X-Process-Time" in response.headers
        # Should be a valid float
        process_time = float(response.headers["X-Process-Time"])
        assert process_time >= 0
    
    def test_successful_request(self, client):
        """Test successful request handling"""
        response = client.get("/test")
        
        assert response.status_code == 200
        assert response.json() == {"message": "success"}
    
    def test_post_request_with_body(self, client):
        """Test POST request with body"""
        response = client.post("/test-post", json={"key": "value"})
        
        assert response.status_code == 200
        assert "X-Request-ID" in response.headers
    
    def test_error_handling(self, client):
        """Test error handling in middleware"""
        response = client.get("/error")
        
        # Should return 500 error
        assert response.status_code == 500
        # Should still have request ID
        assert "X-Request-ID" in response.headers


class TestRequestContextMiddleware:
    """Tests for RequestContextMiddleware class"""
    
    @pytest.fixture
    def app_with_context_middleware(self):
        """Create FastAPI app with context middleware"""
        with patch.dict(os.environ, {
            'FIXEDFLOAT_API_KEY': 'test_key',
            'FIXEDFLOAT_API_SECRET': 'test_secret',
            'RATES_CACHE_ENABLED': 'false'
        }):
            app = FastAPI()
            
            from logging_middleware import RequestContextMiddleware
            
            app.add_middleware(RequestContextMiddleware)
            
            @app.get("/test")
            async def test_endpoint(request: Request):
                return {
                    "has_request_id": hasattr(request.state, 'request_id'),
                    "has_logger": hasattr(request.state, 'logger')
                }
            
            yield app
    
    @pytest.fixture
    def client(self, app_with_context_middleware):
        """Create test client"""
        return TestClient(app_with_context_middleware)
    
    def test_adds_request_id_to_state(self, client):
        """Test that middleware adds request_id to request.state"""
        response = client.get("/test")
        
        assert response.status_code == 200
        data = response.json()
        assert data["has_request_id"] is True
    
    def test_adds_logger_to_state(self, client):
        """Test that middleware adds logger to request.state"""
        response = client.get("/test")
        
        assert response.status_code == 200
        data = response.json()
        assert data["has_logger"] is True


class TestGetRequestLogger:
    """Tests for get_request_logger function"""
    
    def test_get_request_logger_with_logger(self):
        """Test get_request_logger when logger exists in state"""
        from logging_middleware import get_request_logger
        
        mock_request = MagicMock()
        mock_logger = MagicMock()
        mock_request.state.logger = mock_logger
        
        result = get_request_logger(mock_request)
        
        assert result is mock_logger
    
    def test_get_request_logger_without_logger(self):
        """Test get_request_logger when logger doesn't exist"""
        from logging_middleware import get_request_logger
        import logging
        
        mock_request = MagicMock()
        mock_request.state = MagicMock(spec=[])  # No logger attribute
        
        result = get_request_logger(mock_request)
        
        assert isinstance(result, logging.Logger)


class TestGetRequestId:
    """Tests for get_request_id function"""
    
    def test_get_request_id_exists(self):
        """Test get_request_id when request_id exists"""
        from logging_middleware import get_request_id
        
        mock_request = MagicMock()
        mock_request.state.request_id = "test-request-id-123"
        
        result = get_request_id(mock_request)
        
        assert result == "test-request-id-123"
    
    def test_get_request_id_not_exists(self):
        """Test get_request_id when request_id doesn't exist"""
        from logging_middleware import get_request_id
        
        mock_request = MagicMock()
        mock_request.state = MagicMock(spec=[])  # No request_id attribute
        
        result = get_request_id(mock_request)
        
        assert result == "unknown"


class TestClientIPExtraction:
    """Tests for client IP extraction"""
    
    @pytest.fixture
    def app_with_ip_test(self):
        """Create FastAPI app for IP testing"""
        with patch.dict(os.environ, {
            'FIXEDFLOAT_API_KEY': 'test_key',
            'FIXEDFLOAT_API_SECRET': 'test_secret',
            'RATES_CACHE_ENABLED': 'false',
            'LOG_API_REQUESTS': 'true'
        }):
            app = FastAPI()
            
            from logging_middleware import LoggingMiddleware
            
            app.add_middleware(LoggingMiddleware)
            
            @app.get("/test")
            async def test_endpoint():
                return {"status": "ok"}
            
            yield app
    
    @pytest.fixture
    def client(self, app_with_ip_test):
        """Create test client"""
        return TestClient(app_with_ip_test)
    
    def test_extracts_x_forwarded_for(self, client):
        """Test extraction of X-Forwarded-For header"""
        response = client.get("/test", headers={
            "X-Forwarded-For": "192.168.1.1, 10.0.0.1"
        })
        
        assert response.status_code == 200
    
    def test_extracts_x_real_ip(self, client):
        """Test extraction of X-Real-IP header"""
        response = client.get("/test", headers={
            "X-Real-IP": "192.168.1.100"
        })
        
        assert response.status_code == 200


class TestLoggingMiddlewareGetClientIP:
    """Tests for LoggingMiddleware.get_client_ip method"""
    
    def test_get_client_ip_from_forwarded_for(self):
        """Test getting client IP from X-Forwarded-For"""
        from logging_middleware import LoggingMiddleware
        
        middleware = LoggingMiddleware(MagicMock())
        
        mock_request = MagicMock()
        mock_request.headers.get = MagicMock(side_effect=lambda x: {
            "x-forwarded-for": "192.168.1.1, 10.0.0.1",
            "x-real-ip": None
        }.get(x.lower()))
        
        result = middleware.get_client_ip(mock_request)
        
        assert result == "192.168.1.1"
    
    def test_get_client_ip_from_real_ip(self):
        """Test getting client IP from X-Real-IP"""
        from logging_middleware import LoggingMiddleware
        
        middleware = LoggingMiddleware(MagicMock())
        
        mock_request = MagicMock()
        mock_request.headers.get = MagicMock(side_effect=lambda x: {
            "x-forwarded-for": None,
            "x-real-ip": "192.168.1.100"
        }.get(x.lower()))
        
        result = middleware.get_client_ip(mock_request)
        
        assert result == "192.168.1.100"
    
    def test_get_client_ip_from_client(self):
        """Test getting client IP from request.client"""
        from logging_middleware import LoggingMiddleware
        
        middleware = LoggingMiddleware(MagicMock())
        
        mock_request = MagicMock()
        mock_request.headers.get = MagicMock(return_value=None)
        mock_request.client.host = "127.0.0.1"
        
        result = middleware.get_client_ip(mock_request)
        
        assert result == "127.0.0.1"
    
    def test_get_client_ip_unknown(self):
        """Test getting client IP when not available"""
        from logging_middleware import LoggingMiddleware
        
        middleware = LoggingMiddleware(MagicMock())
        
        mock_request = MagicMock()
        mock_request.headers.get = MagicMock(return_value=None)
        mock_request.client = None
        
        result = middleware.get_client_ip(mock_request)
        
        assert result == "unknown"


class TestMakeReceive:
    """Tests for _make_receive helper method"""
    
    @pytest.mark.asyncio
    async def test_make_receive_returns_body(self):
        """Test that _make_receive returns correct body"""
        from logging_middleware import LoggingMiddleware
        
        middleware = LoggingMiddleware(MagicMock())
        
        body = b'{"key": "value"}'
        receive = middleware._make_receive(body)
        
        result = await receive()
        
        assert result["type"] == "http.request"
        assert result["body"] == body
