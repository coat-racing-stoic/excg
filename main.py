from fastapi import FastAPI, HTTPException, Request, Depends, status, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
import time
import json
from datetime import datetime
from typing import List, Optional

from config import settings
from models import *
from auth import get_current_api_key
from rate_limiter import check_rate_limit_middleware, get_rate_limit_headers
from fixedfloat_service import fixedfloat_service
from partner_system import partner_system

# Create FastAPI app
app = FastAPI(
    title="Crypto Exchange Backend API",
    description="Backend API for cryptocurrency exchange using FixedFloat",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

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

# Error handlers
from fastapi.responses import JSONResponse

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "msg": str(exc.detail),
            "data": None
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "msg": f"Internal server error: {str(exc)}",
            "data": None
        }
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