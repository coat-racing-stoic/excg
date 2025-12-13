from fastapi import HTTPException, status
from typing import Optional, Dict, Any

class CryptoExchangeException(Exception):
    """Base exception for crypto exchange operations"""
    
    def __init__(self, message: str, code: int = 500, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)

class AuthenticationError(CryptoExchangeException):
    """Authentication related errors"""
    
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 401, details)

class RateLimitError(CryptoExchangeException):
    """Rate limiting errors"""
    
    def __init__(self, message: str = "Rate limit exceeded", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 429, details)

class ValidationError(CryptoExchangeException):
    """Input validation errors"""
    
    def __init__(self, message: str = "Validation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 400, details)

class FixedFloatAPIError(CryptoExchangeException):
    """FixedFloat API related errors"""
    
    def __init__(self, message: str = "FixedFloat API error", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 502, details)

class OrderNotFoundError(CryptoExchangeException):
    """Order not found errors"""
    
    def __init__(self, order_id: str, details: Optional[Dict[str, Any]] = None):
        message = f"Order {order_id} not found"
        super().__init__(message, 404, details)

class InsufficientFundsError(CryptoExchangeException):
    """Insufficient funds errors"""
    
    def __init__(self, message: str = "Insufficient funds", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 400, details)

class ExchangePairNotSupportedError(CryptoExchangeException):
    """Exchange pair not supported errors"""
    
    def __init__(self, from_currency: str, to_currency: str, details: Optional[Dict[str, Any]] = None):
        message = f"Exchange pair {from_currency} -> {to_currency} not supported"
        super().__init__(message, 400, details)

class MaintenanceError(CryptoExchangeException):
    """Maintenance mode errors"""
    
    def __init__(self, message: str = "Service under maintenance", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, 503, details)

def convert_to_http_exception(exc: CryptoExchangeException) -> HTTPException:
    """Convert custom exception to FastAPI HTTPException"""
    return HTTPException(
        status_code=exc.code,
        detail={
            "error": exc.message,
            "details": exc.details
        }
    )

def handle_fixedfloat_errors(error_codes: list) -> None:
    """Handle FixedFloat API error codes"""
    error_mapping = {
        "MAINTENANCE_FROM": MaintenanceError("Source currency under maintenance"),
        "MAINTENANCE_TO": MaintenanceError("Target currency under maintenance"),
        "LIMIT_MIN": ValidationError("Amount below minimum limit"),
        "LIMIT_MAX": ValidationError("Amount above maximum limit"),
        "PAIR_DISABLED": ExchangePairNotSupportedError("", ""),
        "INSUFFICIENT_FUNDS": InsufficientFundsError(),
        "INVALID_ADDRESS": ValidationError("Invalid destination address"),
        "INVALID_TAG": ValidationError("Invalid memo/destination tag"),
    }
    
    for error_code in error_codes:
        if error_code in error_mapping:
            raise error_mapping[error_code]
    
    # If we have unknown error codes, raise a generic error
    if error_codes:
        raise FixedFloatAPIError(f"FixedFloat API errors: {', '.join(error_codes)}")

def validate_currency_code(currency_code: str) -> None:
    """Validate currency code format"""
    if not currency_code:
        raise ValidationError("Currency code cannot be empty")
    
    if len(currency_code) < 2 or len(currency_code) > 10:
        raise ValidationError("Currency code must be between 2 and 10 characters")
    
    if not currency_code.isalnum():
        raise ValidationError("Currency code must contain only alphanumeric characters")

def validate_address(address: str, currency_code: str) -> None:
    """Validate cryptocurrency address format"""
    if not address:
        raise ValidationError("Address cannot be empty")
    
    # Basic validation - in production, use proper address validation libraries
    if len(address) < 10:
        raise ValidationError("Address too short")
    
    if len(address) > 100:
        raise ValidationError("Address too long")

def validate_amount(amount: float, min_amount: Optional[float] = None, max_amount: Optional[float] = None) -> None:
    """Validate exchange amount"""
    if amount <= 0:
        raise ValidationError("Amount must be positive")
    
    if min_amount and amount < min_amount:
        raise ValidationError(f"Amount {amount} is below minimum {min_amount}")
    
    if max_amount and amount > max_amount:
        raise ValidationError(f"Amount {amount} is above maximum {max_amount}")

def validate_email(email: str) -> None:
    """Validate email address format"""
    import re
    
    if not email:
        raise ValidationError("Email cannot be empty")
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        raise ValidationError("Invalid email format")

def validate_partner_code(refcode: str) -> None:
    """Validate partner referral code"""
    if not refcode:
        raise ValidationError("Partner code cannot be empty")
    
    if len(refcode) < 3 or len(refcode) > 20:
        raise ValidationError("Partner code must be between 3 and 20 characters")
    
    if not refcode.replace('_', '').replace('-', '').isalnum():
        raise ValidationError("Partner code contains invalid characters")