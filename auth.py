import hashlib
import hmac
import json
from typing import Optional, Dict, Any
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from config import settings
from logging_config import get_logger

logger = get_logger('auth')

class APIKeyAuth:
    """Authentication handler for API key and signature verification"""
    
    def __init__(self):
        self.api_keys: Dict[str, str] = {}
        # In production, load API keys from database
        if settings.fixedfloat_api_key and settings.fixedfloat_api_secret:
            self.api_keys[settings.fixedfloat_api_key] = settings.fixedfloat_api_secret
            logger.info(
                "API key loaded from settings",
                extra={
                    'event_type': 'api_key_loaded',
                    'api_key_prefix': settings.fixedfloat_api_key[:8] + '...' if settings.fixedfloat_api_key else None
                }
            )
    
    def add_api_key(self, api_key: str, api_secret: str):
        """Add an API key and secret pair"""
        self.api_keys[api_key] = api_secret
        logger.info(
            "API key added",
            extra={
                'event_type': 'api_key_added',
                'api_key_prefix': api_key[:8] + '...' if api_key else None
            }
        )
    
    def remove_api_key(self, api_key: str) -> bool:
        """Remove an API key"""
        if api_key in self.api_keys:
            del self.api_keys[api_key]
            logger.info(
                "API key removed",
                extra={
                    'event_type': 'api_key_removed',
                    'api_key_prefix': api_key[:8] + '...' if api_key else None
                }
            )
            return True
        return False
    
    def verify_signature(self, api_key: str, signature: str, data: str) -> bool:
        """Verify HMAC-SHA256 signature"""
        if api_key not in self.api_keys:
            logger.warning(
                "Unknown API key attempted authentication",
                extra={
                    'event_type': 'auth_unknown_key',
                    'api_key_prefix': api_key[:8] + '...' if api_key else None
                }
            )
            return False
        
        api_secret = self.api_keys[api_key]
        expected_signature = hmac.new(
            api_secret.encode('utf-8'),
            data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        is_valid = hmac.compare_digest(signature, expected_signature)
        
        if not is_valid:
            logger.warning(
                "Invalid signature for API key",
                extra={
                    'event_type': 'auth_invalid_signature',
                    'api_key_prefix': api_key[:8] + '...' if api_key else None,
                    'provided_signature_prefix': signature[:16] + '...' if signature else None
                }
            )
        
        return is_valid
    
    async def authenticate(self, request: Request) -> Optional[str]:
        """Authenticate request using API key and signature"""
        api_key = request.headers.get("X-API-KEY")
        api_sign = request.headers.get("X-API-SIGN")
        endpoint = request.url.path
        method = request.method
        
        if not api_key or not api_sign:
            logger.warning(
                "Missing authentication headers",
                extra={
                    'event_type': 'auth_missing_headers',
                    'endpoint': endpoint,
                    'method': method,
                    'has_api_key': bool(api_key),
                    'has_api_sign': bool(api_sign)
                }
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing X-API-KEY or X-API-SIGN headers"
            )
        
        # Get request body for signature verification
        body = await request.body()
        body_str = body.decode('utf-8') if body else ""
        
        if not self.verify_signature(api_key, api_sign, body_str):
            logger.warning(
                "Authentication failed",
                extra={
                    'event_type': 'auth_failed',
                    'endpoint': endpoint,
                    'method': method,
                    'api_key_prefix': api_key[:8] + '...' if api_key else None
                }
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API signature"
            )
        
        logger.info(
            "Authentication successful",
            extra={
                'event_type': 'auth_success',
                'endpoint': endpoint,
                'method': method,
                'api_key_prefix': api_key[:8] + '...' if api_key else None
            }
        )
        
        return api_key

# Global auth instance
from config import settings

auth_handler = APIKeyAuth()

# Add configured API key if available
if settings.fixedfloat_api_key and settings.fixedfloat_api_secret:
    auth_handler.add_api_key(settings.fixedfloat_api_key, settings.fixedfloat_api_secret)

# Add demo API key for development mode
if settings.debug:
    auth_handler.add_api_key("demo_api_key", "demo_api_secret")
    logger.info(
        "Demo API key added for development mode",
        extra={'event_type': 'demo_key_added'}
    )

async def get_current_api_key(request: Request) -> str:
    """Dependency to get current authenticated API key"""
    return await auth_handler.authenticate(request)

def create_signature(api_secret: str, data: str) -> str:
    """Create HMAC-SHA256 signature for data"""
    return hmac.new(
        api_secret.encode('utf-8'),
        data.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

def sign_request_data(data: Dict[str, Any], api_secret: str) -> str:
    """Sign request data dictionary"""
    if isinstance(data, dict):
        # Convert dict to JSON string for signing
        json_str = json.dumps(data, separators=(',', ':'), sort_keys=True)
        return create_signature(api_secret, json_str)
    else:
        return create_signature(api_secret, str(data))