from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
from enum import Enum

# Enums for type safety
class ExchangeType(str, Enum):
    FIXED = "fixed"
    FLOAT = "float"

class Direction(str, Enum):
    FROM = "from"
    TO = "to"

class EmergencyChoice(str, Enum):
    EXCHANGE = "EXCHANGE"
    REFUND = "REFUND"

class OrderStatus(str, Enum):
    NEW = "NEW"
    PENDING = "PENDING"
    EXCHANGE = "EXCHANGE"
    WITHDRAW = "WITHDRAW"
    DONE = "DONE"
    EXPIRED = "EXPIRED"
    EMERGENCY = "EMERGENCY"
    FAILED = "FAILED"

# Base response models
class BaseResponse(BaseModel):
    code: int = Field(description="Response code (0 = success)")
    msg: str = Field(description="Response message")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Response data")

class ErrorResponse(BaseModel):
    code: int = Field(description="Error code")
    msg: str = Field(description="Error message")

# Currency models
class Currency(BaseModel):
    code: str = Field(description="Currency code (e.g., BTC, ETH)")
    coin: str = Field(description="Coin symbol")
    network: str = Field(description="Network name")
    name: str = Field(description="Currency full name")
    recv: bool = Field(description="Available for receiving")
    send: bool = Field(description="Available for sending")
    tag: Optional[str] = Field(default=None, description="Tag name (Memo, etc.)")
    logo: str = Field(description="Logo URL")
    color: str = Field(description="Brand color")
    priority: int = Field(description="Display priority")

class CurrenciesResponse(BaseModel):
    currencies: List[Currency] = Field(description="List of supported currencies")

# Exchange rate models
class CurrencyRate(BaseModel):
    code: str = Field(description="Currency code")
    network: str = Field(description="Network name")
    coin: str = Field(description="Coin symbol")
    amount: str = Field(description="Amount as string")
    rate: str = Field(description="Exchange rate as string")
    precision: int = Field(description="Decimal precision")
    min: str = Field(description="Minimum amount")
    max: str = Field(description="Maximum amount")
    usd: str = Field(description="USD equivalent")
    btc: Optional[str] = Field(default=None, description="BTC equivalent")

class ExchangeRate(BaseModel):
    from_rate: CurrencyRate = Field(alias="from", description="Source currency rate")
    to_rate: CurrencyRate = Field(alias="to", description="Target currency rate")
    errors: List[str] = Field(default=[], description="Error codes")
    ccies: Optional[List[Currency]] = Field(default=None, description="Currencies list if requested")

    model_config = {"populate_by_name": True}

# Price calculation models
class PriceRequest(BaseModel):
    type: ExchangeType = Field(description="Exchange type: fixed or float")
    fromCcy: str = Field(description="Source currency code")
    toCcy: str = Field(description="Target currency code")
    direction: Direction = Field(description="Direction: from or to")
    amount: float = Field(gt=0, description="Amount to exchange")
    ccies: Optional[bool] = Field(default=False, description="Include currencies list in response")
    usd: Optional[bool] = Field(default=False, description="Change amount by USD when limits exceeded")
    refcode: Optional[str] = Field(default=None, description="Partner referral code")
    afftax: Optional[float] = Field(default=None, ge=0, le=100, description="Partner commission percentage")

# Transaction models
class Transaction(BaseModel):
    id: Optional[str] = Field(default=None, description="Transaction hash")
    amount: Optional[str] = Field(default=None, description="Transaction amount")
    fee: Optional[str] = Field(default=None, description="Network fee")
    ccyfee: Optional[str] = Field(default=None, description="Fee currency")
    timeReg: Optional[int] = Field(default=None, description="Registration timestamp")
    timeBlock: Optional[int] = Field(default=None, description="Block inclusion timestamp")
    confirmations: Optional[int] = Field(default=None, description="Number of confirmations")

# Emergency models
class Emergency(BaseModel):
    status: List[str] = Field(description="Emergency status codes")
    choice: str = Field(description="Emergency choice: NONE, EXCHANGE, REFUND")
    repeat: bool = Field(description="Is repeat transaction")

# Time data models
class TimeData(BaseModel):
    reg: int = Field(description="Order creation timestamp")
    start: Optional[int] = Field(default=None, description="Transaction received timestamp")
    finish: Optional[int] = Field(default=None, description="Order completion timestamp")
    update: int = Field(description="Last update timestamp")
    expiration: int = Field(description="Expiration timestamp")
    left: int = Field(description="Seconds left until expiration")

# Order currency models
class OrderCurrency(BaseModel):
    code: str = Field(description="Currency code")
    coin: str = Field(description="Coin symbol")
    network: str = Field(description="Network name")
    name: str = Field(description="Currency name")
    alias: str = Field(description="Currency alias")
    amount: str = Field(description="Amount as string")
    address: str = Field(description="Wallet address")
    addressAlt: Optional[str] = Field(default=None, description="Alternative address")
    tag: Optional[str] = Field(default=None, description="MEMO/Destination Tag")
    tagName: Optional[str] = Field(default=None, description="Tag name")
    reqConfirmations: int = Field(description="Required confirmations")
    maxConfirmations: int = Field(description="Maximum confirmations")
    tx: Transaction = Field(description="Transaction data")

# Order creation models
class CreateOrderRequest(PriceRequest):
    toAddress: str = Field(description="Destination address for receiving funds")
    tag: Optional[str] = Field(default=None, description="MEMO/Destination Tag if required")

class Order(BaseModel):
    id: str = Field(description="Order ID")
    type: str = Field(description="Order type: fixed or float")
    email: str = Field(description="Email for notifications")
    status: OrderStatus = Field(description="Current order status")
    time: TimeData = Field(description="Time data")
    from_currency: OrderCurrency = Field(alias="from", description="Source currency data")
    to_currency: OrderCurrency = Field(alias="to", description="Target currency data")
    back: Optional[OrderCurrency] = Field(default=None, description="Refund currency data")
    emergency: Emergency = Field(description="Emergency data")
    token: str = Field(description="Security token")

    model_config = {"populate_by_name": True}

# Order status models
class OrderStatusRequest(BaseModel):
    id: str = Field(description="Order ID")
    token: str = Field(description="Security token")

class OrderStatusResponse(BaseModel):
    id: str = Field(description="Order ID")
    status: OrderStatus = Field(description="Current order status")
    from_currency: str = Field(description="Source currency")
    to_currency: str = Field(description="Target currency")
    from_amount: float = Field(description="Source amount")
    to_amount: float = Field(description="Target amount")
    from_address: str = Field(description="Address to send funds to")
    to_address: str = Field(description="Address to receive funds")
    tx_from: Optional[str] = Field(default=None, description="Source transaction hash")
    tx_to: Optional[str] = Field(default=None, description="Destination transaction hash")
    created_at: Optional[str] = Field(default=None, description="Order creation timestamp")
    expires_at: Optional[str] = Field(default=None, description="Order expiration timestamp")

# Emergency handling models
class EmergencyRequest(BaseModel):
    id: str = Field(description="Order ID")
    token: str = Field(description="Security token")
    choice: EmergencyChoice = Field(description="Emergency action choice")
    address: Optional[str] = Field(default=None, description="Refund address (required for REFUND)")
    tag: Optional[str] = Field(default=None, description="MEMO/Destination Tag for refund")

class EmergencyResponse(BaseModel):
    id: str = Field(description="Order ID")
    choice: EmergencyChoice = Field(description="Selected emergency action")
    status: str = Field(description="Emergency action status")
    message: str = Field(description="Emergency action result message")

# Email notification models
class SetEmailRequest(BaseModel):
    id: str = Field(description="Order ID")
    token: str = Field(description="Security token")
    email: str = Field(description="Email address for notifications")

class SetEmailResponse(BaseModel):
    id: str = Field(description="Order ID")
    email: str = Field(description="Email address set for notifications")
    status: str = Field(description="Email setting status")

# QR code models
class QRRequest(BaseModel):
    id: str = Field(description="Order ID")
    token: str = Field(description="Security token")

class QRCode(BaseModel):
    title: str = Field(description="QR code title")
    src: str = Field(description="Base64 encoded QR code image")
    checked: bool = Field(description="Is selected by default")

class QRResponse(BaseModel):
    qr_codes: List[QRCode] = Field(description="List of QR codes")

# XML Rate models
class XMLRate(BaseModel):
    from_currency: str = Field(alias="from", description="Source currency")
    to_currency: str = Field(alias="to", description="Target currency")
    in_amount: float = Field(alias="in", description="Input amount")
    out_amount: float = Field(alias="out", description="Output amount")
    amount: float = Field(description="Base amount")
    fee: Optional[str] = Field(alias="tofee", default=None, description="Fee information")
    min_amount: Optional[str] = Field(alias="minamount", default=None, description="Minimum amount")
    max_amount: Optional[str] = Field(alias="maxamount", default=None, description="Maximum amount")

    model_config = {"populate_by_name": True}

# Partner system models
class PartnerCalculation(BaseModel):
    refcode: str = Field(description="Partner referral code")
    afftax: float = Field(description="Partner commission percentage")
    total_commission: float = Field(description="Calculated total commission")
    formula_used: str = Field(description="Formula used for calculation")

# Rate limiting models
class RateLimitInfo(BaseModel):
    requests_remaining: int = Field(description="Remaining requests in current window")
    reset_time: int = Field(description="Time when rate limit resets (Unix timestamp)")
    weight_used: int = Field(description="Weight used for current request")

# Health check model
class HealthResponse(BaseModel):
    status: str = Field(description="Service status")
    timestamp: str = Field(description="Current timestamp")
    version: str = Field(description="API version")