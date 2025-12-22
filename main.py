from fastapi import FastAPI, HTTPException, Request, Depends, status, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from contextlib import asynccontextmanager
import time
import json
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from config import settings
from models import *
from auth import get_current_api_key
from rate_limiter import check_rate_limit_middleware, get_rate_limit_headers
from fixedfloat_service import fixedfloat_service
from partner_system import partner_system
from logging_config import LoggingConfig, get_logger, log_error
from logging_middleware import LoggingMiddleware, RequestContextMiddleware, get_request_logger, get_request_id

# Initialize logging
logging_config = LoggingConfig(log_dir=settings.log_dir, debug=settings.debug)
logging_config.setup_logging()

# Get logger
logger = get_logger('app')

# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Startup
    logger.info("Starting application...")
    
    # Запускаем фоновое обновление курсов если кэширование включено
    if settings.rates_cache_enabled:
        try:
            from rates_updater import rates_updater
            await rates_updater.start()
            logger.info(
                f"Rates updater started with {settings.rates_update_interval}s interval",
                extra={'event_type': 'rates_updater_started'}
            )
        except Exception as e:
            logger.error(
                f"Failed to start rates updater: {e}",
                extra={'event_type': 'rates_updater_error', 'error': str(e)}
            )
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    
    # Останавливаем фоновое обновление курсов
    if settings.rates_cache_enabled:
        try:
            from rates_updater import rates_updater
            await rates_updater.stop()
            logger.info("Rates updater stopped", extra={'event_type': 'rates_updater_stopped'})
        except Exception as e:
            logger.error(
                f"Error stopping rates updater: {e}",
                extra={'event_type': 'rates_updater_error', 'error': str(e)}
            )

# Create FastAPI app
app = FastAPI(
    title="Crypto Exchange Backend API",
    description="Backend API for cryptocurrency exchange using FixedFloat",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add logging middleware (first to catch all requests)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RequestContextMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        version="1.0.0"
    )

# Authenticated API endpoints
@app.post("/api/v2/ccies", response_model=BaseResponse)
async def get_currencies(
    request: Request,
    api_key: str = Depends(get_current_api_key)
):
    """
    Get list of supported currencies
    
    Weight: 1 unit
    Authentication: Required (X-API-KEY and X-API-SIGN)
    """
    try:
        # Check rate limits
        await check_rate_limit_middleware(request, api_key)
        
        # Get currencies from FixedFloat
        currencies = await fixedfloat_service.get_currencies()
        
        # Prepare response
        response_data = {
            "code": 0,
            "msg": "Success",
            "data": [currency.dict() for currency in currencies]
        }
        
        # Add rate limit headers
        headers = get_rate_limit_headers(api_key)
        
        return Response(
            content=json.dumps(response_data),
            media_type="application/json",
            headers=headers
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@app.post("/api/v2/price", response_model=BaseResponse)
async def get_exchange_rate(
    price_request: PriceRequest,
    request: Request,
    api_key: str = Depends(get_current_api_key)
):
    """
    Calculate exchange rate for currency pair
    
    Weight: 1 unit
    Authentication: Required (X-API-KEY and X-API-SIGN)
    """
    try:
        # Check rate limits
        await check_rate_limit_middleware(request, api_key)
        
        # Validate partner parameters
        if not partner_system.validate_partner_request(price_request.refcode, price_request.afftax):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid partner parameters"
            )
        
        # Get exchange rate from FixedFloat
        exchange_rate = await fixedfloat_service.get_exchange_rate(price_request)
        
        # Calculate partner commission if applicable
        partner_calculation = None
        if price_request.refcode and price_request.afftax:
            # Demo values for FF and AFFB
            ff = 2.0  # FixedFloat fee
            affb = 0.5  # Affiliate base commission
            partner_calculation = partner_system.calculate_commission(
                price_request.refcode, price_request.afftax, ff, affb
            )
        
        # Prepare response
        response_data = {
            "code": 0,
            "msg": "Success",
            "data": {
                "exchange_rate": exchange_rate.dict(),
                "partner_calculation": partner_calculation.dict() if partner_calculation else None
            }
        }
        
        # Add rate limit headers
        headers = get_rate_limit_headers(api_key)
        
        return Response(
            content=BaseResponse(**response_data).json(),
            media_type="application/json",
            headers=headers
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@app.post("/api/v2/create", response_model=BaseResponse)
async def create_order(
    create_request: CreateOrderRequest,
    request: Request,
    api_key: str = Depends(get_current_api_key)
):
    """
    Create new exchange order
    
    Weight: 50 units
    Authentication: Required (X-API-KEY and X-API-SIGN)
    """
    try:
        # Check rate limits
        await check_rate_limit_middleware(request, api_key)
        
        # Validate partner parameters
        if not partner_system.validate_partner_request(create_request.refcode, create_request.afftax):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid partner parameters"
            )
        
        # Create order via FixedFloat
        order = await fixedfloat_service.create_order(create_request)
        
        # Prepare response
        response_data = {
            "code": 0,
            "msg": "Success",
            "data": order.dict()
        }
        
        # Add rate limit headers
        headers = get_rate_limit_headers(api_key)
        
        return Response(
            content=BaseResponse(**response_data).json(),
            media_type="application/json",
            headers=headers
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@app.post("/api/v2/order", response_model=BaseResponse)
async def get_order_status(
    order_request: OrderStatusRequest,
    request: Request,
    api_key: str = Depends(get_current_api_key)
):
    """
    Get order status and information
    
    Weight: 1 unit
    Authentication: Required (X-API-KEY and X-API-SIGN)
    """
    try:
        # Check rate limits
        await check_rate_limit_middleware(request, api_key)
        
        # Get order status from FixedFloat
        order = await fixedfloat_service.get_order_status(order_request)
        
        # Prepare response
        response_data = {
            "code": 0,
            "msg": "Success",
            "data": order.dict()
        }
        
        # Add rate limit headers
        headers = get_rate_limit_headers(api_key)
        
        return Response(
            content=BaseResponse(**response_data).json(),
            media_type="application/json",
            headers=headers
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@app.post("/api/v2/emergency", response_model=BaseResponse)
async def handle_emergency(
    emergency_request: EmergencyRequest,
    request: Request,
    api_key: str = Depends(get_current_api_key)
):
    """
    Handle emergency situation for order
    
    Weight: 1 unit
    Authentication: Required (X-API-KEY and X-API-SIGN)
    """
    try:
        # Check rate limits
        await check_rate_limit_middleware(request, api_key)
        
        # Handle emergency via FixedFloat
        emergency_response = await fixedfloat_service.handle_emergency(emergency_request)
        
        # Prepare response
        response_data = {
            "code": 0,
            "msg": "Success",
            "data": emergency_response.dict()
        }
        
        # Add rate limit headers
        headers = get_rate_limit_headers(api_key)
        
        return Response(
            content=BaseResponse(**response_data).json(),
            media_type="application/json",
            headers=headers
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@app.post("/api/v2/setEmail", response_model=BaseResponse)
async def set_email_notification(
    email_request: SetEmailRequest,
    request: Request,
    api_key: str = Depends(get_current_api_key)
):
    """
    Set email address for order notifications
    
    Weight: 1 unit
    Authentication: Required (X-API-KEY and X-API-SIGN)
    """
    try:
        # Check rate limits
        await check_rate_limit_middleware(request, api_key)
        
        # Set email via FixedFloat
        email_response = await fixedfloat_service.set_email(email_request)
        
        # Prepare response
        response_data = {
            "code": 0,
            "msg": "Success",
            "data": email_response.dict()
        }
        
        # Add rate limit headers
        headers = get_rate_limit_headers(api_key)
        
        return Response(
            content=BaseResponse(**response_data).json(),
            media_type="application/json",
            headers=headers
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@app.post("/api/v2/qr", response_model=BaseResponse)
async def get_qr_codes(
    qr_request: QRRequest,
    request: Request,
    api_key: str = Depends(get_current_api_key)
):
    """
    Get QR codes for order
    
    Weight: 1 unit
    Authentication: Required (X-API-KEY and X-API-SIGN)
    """
    try:
        # Check rate limits
        await check_rate_limit_middleware(request, api_key)
        
        # Get QR codes via FixedFloat
        qr_response = await fixedfloat_service.get_qr_codes(qr_request)
        
        # Prepare response
        response_data = {
            "code": 0,
            "msg": "Success",
            "data": qr_response.dict()
        }
        
        # Add rate limit headers
        headers = get_rate_limit_headers(api_key)
        
        return Response(
            content=BaseResponse(**response_data).json(),
            media_type="application/json",
            headers=headers
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

# Free XML endpoints (no authentication required)
@app.get("/rates/fixed.xml", response_class=PlainTextResponse)
async def get_fixed_rates_xml():
    """
    Get fixed exchange rates in XML format
    
    Authentication: Not required
    Rate limits: Unlimited
    Recommended: Cache locally with TTL 5-10 minutes
    """
    try:
        xml_content = await fixedfloat_service.get_fixed_rates_xml(parse=False)
        return PlainTextResponse(content=xml_content, media_type="application/xml")
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get fixed rates XML: {str(e)}"
        )

@app.get("/rates/float.xml", response_class=PlainTextResponse)
async def get_float_rates_xml():
    """
    Get floating exchange rates in XML format
    
    Authentication: Not required
    Rate limits: Unlimited
    Recommended: Cache locally with TTL 5-10 minutes
    """
    try:
        xml_content = await fixedfloat_service.get_float_rates_xml(parse=False)
        return PlainTextResponse(content=xml_content, media_type="application/xml")
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get float rates XML: {str(e)}"
        )

# Parsed XML endpoints for easier consumption
@app.get("/api/rates/fixed", response_model=List[XMLRate])
async def get_fixed_rates_parsed():
    """
    Get fixed exchange rates in JSON format (parsed from XML)
    
    Authentication: Not required
    Rate limits: Unlimited
    """
    try:
        rates = await fixedfloat_service.get_fixed_rates_xml(parse=True)
        return rates
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get fixed rates: {str(e)}"
        )

@app.get("/api/rates/float", response_model=List[XMLRate])
async def get_float_rates_parsed():
    """
    Get floating exchange rates in JSON format (parsed from XML)
    
    Authentication: Not required
    Rate limits: Unlimited
    """
    try:
        rates = await fixedfloat_service.get_float_rates_xml(parse=True)
        return rates
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get float rates: {str(e)}"
        )

# Cache management endpoints
@app.get("/api/cache/status")
async def get_cache_status():
    """
    Get rates cache status
    
    Returns information about cached rates including:
    - Connection status
    - Number of cached rates
    - Last update timestamps
    - TTL remaining
    
    Authentication: Not required
    """
    try:
        if not settings.rates_cache_enabled:
            return {
                "enabled": False,
                "message": "Rates caching is disabled"
            }
        
        from redis_cache import rates_cache
        from rates_updater import rates_updater
        
        cache_status = await rates_cache.get_cache_status()
        updater_status = rates_updater.get_status()
        
        return {
            "enabled": True,
            "cache": cache_status,
            "updater": updater_status,
            "config": {
                "update_interval_seconds": settings.rates_update_interval,
                "cache_ttl_seconds": settings.rates_cache_ttl
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cache status: {str(e)}"
        )

@app.post("/api/cache/refresh")
async def refresh_cache():
    """
    Force refresh of rates cache
    
    Triggers immediate update of both fixed and float rates from FixedFloat API.
    
    Authentication: Not required (consider adding auth in production)
    """
    try:
        if not settings.rates_cache_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Rates caching is disabled"
            )
        
        from rates_updater import rates_updater
        
        result = await rates_updater.force_update()
        
        return {
            "code": 0,
            "msg": "Cache refresh completed",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh cache: {str(e)}"
        )

@app.get("/api/rates/pair/{from_currency}/{to_currency}")
async def get_rate_for_pair(
    from_currency: str,
    to_currency: str,
    rate_type: str = "fixed"
):
    """
    Get cached exchange rate for specific currency pair
    
    Args:
        from_currency: Source currency code (e.g., BTC)
        to_currency: Target currency code (e.g., ETH)
        rate_type: "fixed" or "float" (default: "fixed")
    
    Returns cached rate if available, otherwise fetches from API.
    
    Authentication: Not required
    """
    try:
        # Пробуем получить из кэша
        cached_rate = await fixedfloat_service.get_cached_rate_for_pair(
            from_currency.upper(),
            to_currency.upper(),
            rate_type
        )
        
        if cached_rate:
            return {
                "code": 0,
                "msg": "Success",
                "data": {
                    "rate": cached_rate.dict(by_alias=True),
                    "source": "cache"
                }
            }
        
        # Если нет в кэше, ищем в полном списке
        if rate_type == "fixed":
            rates = await fixedfloat_service.get_fixed_rates_xml(parse=True, use_cache=True)
        else:
            rates = await fixedfloat_service.get_float_rates_xml(parse=True, use_cache=True)
        
        for rate in rates:
            rate_dict = rate.dict(by_alias=True)
            if rate_dict.get('from') == from_currency.upper() and rate_dict.get('to') == to_currency.upper():
                return {
                    "code": 0,
                    "msg": "Success",
                    "data": {
                        "rate": rate_dict,
                        "source": "api"
                    }
                }
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rate for pair {from_currency}->{to_currency} not found"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get rate for pair: {str(e)}"
        )

# Error handlers
from fastapi.responses import JSONResponse

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with logging"""
    request_logger = get_request_logger(request)
    request_id = get_request_id(request)
    
    # Логируем HTTP исключения
    request_logger.warning(
        f"HTTP Exception: {exc.status_code} - {exc.detail}",
        extra={
            'request_id': request_id,
            'status_code': exc.status_code,
            'error_type': 'HTTPException',
            'error_details': str(exc.detail),
            'endpoint': request.url.path,
            'method': request.method,
            'event_type': 'http_exception'
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "msg": str(exc.detail),
            "data": None
        },
        headers={"X-Request-ID": request_id}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions with detailed logging"""
    request_logger = get_request_logger(request)
    request_id = get_request_id(request)
    
    # Логируем общие исключения с полной трассировкой
    log_error(
        request_logger,
        error=exc,
        request_id=request_id,
        context={
            'endpoint': request.url.path,
            'method': request.method,
            'client_ip': request.client.host if request.client else 'unknown',
            'user_agent': request.headers.get('user-agent', 'unknown'),
            'api_key': request.headers.get('x-api-key', 'none')[:8] + '...' if request.headers.get('x-api-key') else None
        }
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "msg": "Internal server error",
            "data": {
                "error": "An unexpected error occurred",
                "request_id": request_id
            }
        },
        headers={"X-Request-ID": request_id}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        access_log=True
    )