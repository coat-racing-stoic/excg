import hashlib
import hmac
import json
from typing import Optional, Dict, Any
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from config import settings

class APIKeyAuth:
    """Authentication handler for API key and signature verification"""
    
    def __init__(self):
        self.api_keys: Dict[str, str] = {}
        # In production, load API keys from database
        if settings.fixedfloat_api_key and settings.fixedfloat_api_secret:
            self.api_keys[settings.fixedfloat_api_key] = settings.fixedfloat_api_secret
    
    def add_api_key(self, api_key: str, api_secret: str):
        """Add an API key and secret pair"""
        self.api_keys[api_key] = api_secret
    
    def verify_signature(self, api_key: str, signature: str, data: str) -> bool:
        """Verify HMAC-SHA256 signature"""
        if api_key not in self.api_keys:
            return False
        
        api_secret = self.api_keys[api_key]
        expected_signature = hmac.new(
            api_secret.encode('utf-8'),
            data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    async def authenticate(self, request: Request) -> Optional[str]:
        """Authenticate request using API key and signature"""
        api_key = request.headers.get("X-API-KEY")
        api_sign = request.headers.get("X-API-SIGN")
        
        if not api_key or not api_sign:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing X-API-KEY or X-API-SIGN headers"
            )
        
        # Get request body for signature verification
        body = await request.body()
        body_str = body.decode('utf-8') if body else ""
        

        
        if not self.verify_signature(api_key, api_sign, body_str):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API signature"
            )
        
        return api_key

# Global auth instance
from config import settings

auth_handler = APIKeyAuth()
auth_handler.add_api_key(settings.fixedfloat_api_key, settings.fixedfloat_api_secret)

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