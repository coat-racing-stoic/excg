"""
Tests for auth.py - Authentication module
"""
import pytest
import hmac
import hashlib
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import HTTPException

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestAPIKeyAuth:
    """Tests for APIKeyAuth class"""
    
    def test_init_with_credentials(self):
        """Test initialization with API credentials"""
        with patch('auth.settings') as mock_settings:
            mock_settings.fixedfloat_api_key = "test_key"
            mock_settings.fixedfloat_api_secret = "test_secret"
            
            from auth import APIKeyAuth
            auth = APIKeyAuth()
            
            assert "test_key" in auth.api_keys
            assert auth.api_keys["test_key"] == "test_secret"
    
    def test_init_without_credentials(self):
        """Test initialization without API credentials"""
        with patch('auth.settings') as mock_settings:
            mock_settings.fixedfloat_api_key = None
            mock_settings.fixedfloat_api_secret = None
            
            from auth import APIKeyAuth
            auth = APIKeyAuth()
            
            assert len(auth.api_keys) == 0
    
    def test_add_api_key(self):
        """Test adding API key"""
        with patch('auth.settings') as mock_settings:
            mock_settings.fixedfloat_api_key = None
            mock_settings.fixedfloat_api_secret = None
            
            from auth import APIKeyAuth
            auth = APIKeyAuth()
            
            auth.add_api_key("new_key", "new_secret")
            
            assert "new_key" in auth.api_keys
            assert auth.api_keys["new_key"] == "new_secret"
    
    def test_remove_api_key(self):
        """Test removing API key"""
        with patch('auth.settings') as mock_settings:
            mock_settings.fixedfloat_api_key = "test_key"
            mock_settings.fixedfloat_api_secret = "test_secret"
            
            from auth import APIKeyAuth
            auth = APIKeyAuth()
            
            result = auth.remove_api_key("test_key")
            
            assert result is True
            assert "test_key" not in auth.api_keys
    
    def test_remove_nonexistent_api_key(self):
        """Test removing non-existent API key"""
        with patch('auth.settings') as mock_settings:
            mock_settings.fixedfloat_api_key = None
            mock_settings.fixedfloat_api_secret = None
            
            from auth import APIKeyAuth
            auth = APIKeyAuth()
            
            result = auth.remove_api_key("nonexistent_key")
            
            assert result is False
    
    def test_verify_signature_valid(self):
        """Test signature verification with valid signature"""
        with patch('auth.settings') as mock_settings:
            mock_settings.fixedfloat_api_key = "test_key"
            mock_settings.fixedfloat_api_secret = "test_secret"
            
            from auth import APIKeyAuth
            auth = APIKeyAuth()
            
            data = "test_data"
            signature = hmac.new(
                "test_secret".encode('utf-8'),
                data.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            result = auth.verify_signature("test_key", signature, data)
            
            assert result is True
    
    def test_verify_signature_invalid(self):
        """Test signature verification with invalid signature"""
        with patch('auth.settings') as mock_settings:
            mock_settings.fixedfloat_api_key = "test_key"
            mock_settings.fixedfloat_api_secret = "test_secret"
            
            from auth import APIKeyAuth
            auth = APIKeyAuth()
            
            result = auth.verify_signature("test_key", "invalid_signature", "test_data")
            
            assert result is False
    
    def test_verify_signature_unknown_key(self):
        """Test signature verification with unknown API key"""
        with patch('auth.settings') as mock_settings:
            mock_settings.fixedfloat_api_key = "test_key"
            mock_settings.fixedfloat_api_secret = "test_secret"
            
            from auth import APIKeyAuth
            auth = APIKeyAuth()
            
            result = auth.verify_signature("unknown_key", "any_signature", "test_data")
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_authenticate_missing_headers(self):
        """Test authentication with missing headers"""
        with patch('auth.settings') as mock_settings:
            mock_settings.fixedfloat_api_key = "test_key"
            mock_settings.fixedfloat_api_secret = "test_secret"
            
            from auth import APIKeyAuth
            auth = APIKeyAuth()
            
            # Mock request without headers
            mock_request = MagicMock()
            mock_request.headers = {}
            mock_request.headers.get = MagicMock(return_value=None)
            mock_request.url.path = "/api/v2/test"
            mock_request.method = "POST"
            
            with pytest.raises(HTTPException) as exc_info:
                await auth.authenticate(mock_request)
            
            assert exc_info.value.status_code == 401
            assert "Missing X-API-KEY or X-API-SIGN headers" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_authenticate_invalid_signature(self):
        """Test authentication with invalid signature"""
        with patch('auth.settings') as mock_settings:
            mock_settings.fixedfloat_api_key = "test_key"
            mock_settings.fixedfloat_api_secret = "test_secret"
            
            from auth import APIKeyAuth
            auth = APIKeyAuth()
            
            # Mock request with invalid signature
            mock_request = MagicMock()
            mock_request.headers.get = MagicMock(side_effect=lambda x: {
                "X-API-KEY": "test_key",
                "X-API-SIGN": "invalid_signature"
            }.get(x))
            mock_request.url.path = "/api/v2/test"
            mock_request.method = "POST"
            mock_request.body = AsyncMock(return_value=b"")
            
            with pytest.raises(HTTPException) as exc_info:
                await auth.authenticate(mock_request)
            
            assert exc_info.value.status_code == 401
            assert "Invalid API signature" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_authenticate_success(self):
        """Test successful authentication"""
        with patch('auth.settings') as mock_settings:
            mock_settings.fixedfloat_api_key = "test_key"
            mock_settings.fixedfloat_api_secret = "test_secret"
            
            from auth import APIKeyAuth
            auth = APIKeyAuth()
            
            # Create valid signature
            body = ""
            signature = hmac.new(
                "test_secret".encode('utf-8'),
                body.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Mock request with valid credentials
            mock_request = MagicMock()
            mock_request.headers.get = MagicMock(side_effect=lambda x: {
                "X-API-KEY": "test_key",
                "X-API-SIGN": signature
            }.get(x))
            mock_request.url.path = "/api/v2/test"
            mock_request.method = "POST"
            mock_request.body = AsyncMock(return_value=b"")
            
            result = await auth.authenticate(mock_request)
            
            assert result == "test_key"


class TestSignatureFunctions:
    """Tests for signature helper functions"""
    
    def test_create_signature(self):
        """Test create_signature function"""
        from auth import create_signature
        
        api_secret = "test_secret"
        data = "test_data"
        
        expected = hmac.new(
            api_secret.encode('utf-8'),
            data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        result = create_signature(api_secret, data)
        
        assert result == expected
    
    def test_create_signature_empty_data(self):
        """Test create_signature with empty data"""
        from auth import create_signature
        
        api_secret = "test_secret"
        data = ""
        
        expected = hmac.new(
            api_secret.encode('utf-8'),
            data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        result = create_signature(api_secret, data)
        
        assert result == expected
    
    def test_sign_request_data_dict(self):
        """Test sign_request_data with dictionary"""
        from auth import sign_request_data
        import json
        
        api_secret = "test_secret"
        data = {"key": "value", "number": 123}
        
        json_str = json.dumps(data, separators=(',', ':'), sort_keys=True)
        expected = hmac.new(
            api_secret.encode('utf-8'),
            json_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        result = sign_request_data(data, api_secret)
        
        assert result == expected
    
    def test_sign_request_data_string(self):
        """Test sign_request_data with string"""
        from auth import sign_request_data
        
        api_secret = "test_secret"
        data = "test_string"
        
        expected = hmac.new(
            api_secret.encode('utf-8'),
            data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        result = sign_request_data(data, api_secret)
        
        assert result == expected


class TestGetCurrentApiKey:
    """Tests for get_current_api_key dependency"""
    
    @pytest.mark.asyncio
    async def test_get_current_api_key_success(self):
        """Test get_current_api_key with valid credentials"""
        with patch('auth.settings') as mock_settings:
            mock_settings.fixedfloat_api_key = "test_key"
            mock_settings.fixedfloat_api_secret = "test_secret"
            
            # Reload auth module to apply patched settings
            import importlib
            import auth
            importlib.reload(auth)
            
            # Create valid signature
            body = ""
            signature = hmac.new(
                "test_secret".encode('utf-8'),
                body.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Mock request
            mock_request = MagicMock()
            mock_request.headers.get = MagicMock(side_effect=lambda x: {
                "X-API-KEY": "test_key",
                "X-API-SIGN": signature
            }.get(x))
            mock_request.url.path = "/api/v2/test"
            mock_request.method = "POST"
            mock_request.body = AsyncMock(return_value=b"")
            
            result = await auth.get_current_api_key(mock_request)
            
            assert result == "test_key"
