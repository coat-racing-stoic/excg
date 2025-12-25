"""Mock data for development mode when FixedFloat API is not configured"""

from typing import List, Dict, Any
from models import Currency, ExchangeRate, CurrencyRate, Order, OrderStatus, TimeData, OrderCurrency, Transaction, Emergency
import time
import uuid

# Mock currencies data
MOCK_CURRENCIES: List[Dict[str, Any]] = [
    {
        "code": "BTC",
        "coin": "BTC",
        "network": "BTC",
        "name": "Bitcoin",
        "recv": True,
        "send": True,
        "tag": None,
        "logo": "https://fixedfloat.com/assets/images/coins/btc.svg",
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
        "logo": "https://fixedfloat.com/assets/images/coins/eth.svg",
        "color": "#627EEA",
        "priority": 99
    },
    {
        "code": "USDTTRC",
        "coin": "USDT",
        "network": "TRC20",
        "name": "Tether TRC20",
        "recv": True,
        "send": True,
        "tag": None,
        "logo": "https://fixedfloat.com/assets/images/coins/usdt.svg",
        "color": "#26A17B",
        "priority": 98
    },
    {
        "code": "USDTERC",
        "coin": "USDT",
        "network": "ERC20",
        "name": "Tether ERC20",
        "recv": True,
        "send": True,
        "tag": None,
        "logo": "https://fixedfloat.com/assets/images/coins/usdt.svg",
        "color": "#26A17B",
        "priority": 97
    },
    {
        "code": "USDC",
        "coin": "USDC",
        "network": "ERC20",
        "name": "USD Coin",
        "recv": True,
        "send": True,
        "tag": None,
        "logo": "https://fixedfloat.com/assets/images/coins/usdc.svg",
        "color": "#2775CA",
        "priority": 96
    },
    {
        "code": "BNB",
        "coin": "BNB",
        "network": "BSC",
        "name": "BNB",
        "recv": True,
        "send": True,
        "tag": None,
        "logo": "https://fixedfloat.com/assets/images/coins/bnb.svg",
        "color": "#F3BA2F",
        "priority": 95
    },
    {
        "code": "SOL",
        "coin": "SOL",
        "network": "SOL",
        "name": "Solana",
        "recv": True,
        "send": True,
        "tag": None,
        "logo": "https://fixedfloat.com/assets/images/coins/sol.svg",
        "color": "#00FFA3",
        "priority": 94
    },
    {
        "code": "XRP",
        "coin": "XRP",
        "network": "XRP",
        "name": "Ripple",
        "recv": True,
        "send": True,
        "tag": "Destination Tag",
        "logo": "https://fixedfloat.com/assets/images/coins/xrp.svg",
        "color": "#23292F",
        "priority": 93
    },
    {
        "code": "DOGE",
        "coin": "DOGE",
        "network": "DOGE",
        "name": "Dogecoin",
        "recv": True,
        "send": True,
        "tag": None,
        "logo": "https://fixedfloat.com/assets/images/coins/doge.svg",
        "color": "#C2A633",
        "priority": 92
    },
    {
        "code": "LTC",
        "coin": "LTC",
        "network": "LTC",
        "name": "Litecoin",
        "recv": True,
        "send": True,
        "tag": None,
        "logo": "https://fixedfloat.com/assets/images/coins/ltc.svg",
        "color": "#BFBBBB",
        "priority": 91
    },
    {
        "code": "TRX",
        "coin": "TRX",
        "network": "TRX",
        "name": "TRON",
        "recv": True,
        "send": True,
        "tag": None,
        "logo": "https://fixedfloat.com/assets/images/coins/trx.svg",
        "color": "#FF0013",
        "priority": 90
    },
    {
        "code": "MATIC",
        "coin": "MATIC",
        "network": "POLYGON",
        "name": "Polygon",
        "recv": True,
        "send": True,
        "tag": None,
        "logo": "https://fixedfloat.com/assets/images/coins/matic.svg",
        "color": "#8247E5",
        "priority": 89
    },
    {
        "code": "TON",
        "coin": "TON",
        "network": "TON",
        "name": "Toncoin",
        "recv": True,
        "send": True,
        "tag": "Memo",
        "logo": "https://fixedfloat.com/assets/images/coins/ton.svg",
        "color": "#0098EA",
        "priority": 88
    },
    {
        "code": "AVAX",
        "coin": "AVAX",
        "network": "AVAX",
        "name": "Avalanche",
        "recv": True,
        "send": True,
        "tag": None,
        "logo": "https://fixedfloat.com/assets/images/coins/avax.svg",
        "color": "#E84142",
        "priority": 87
    },
    {
        "code": "ADA",
        "coin": "ADA",
        "network": "ADA",
        "name": "Cardano",
        "recv": True,
        "send": True,
        "tag": None,
        "logo": "https://fixedfloat.com/assets/images/coins/ada.svg",
        "color": "#0033AD",
        "priority": 86
    }
]

# Mock exchange rates (approximate values)
MOCK_RATES: Dict[str, Dict[str, float]] = {
    "BTC": {"USD": 98500, "min": 0.0001, "max": 10},
    "ETH": {"USD": 3450, "min": 0.01, "max": 100},
    "USDTTRC": {"USD": 1.0, "min": 10, "max": 100000},
    "USDTERC": {"USD": 1.0, "min": 10, "max": 100000},
    "USDC": {"USD": 1.0, "min": 10, "max": 100000},
    "BNB": {"USD": 695, "min": 0.1, "max": 500},
    "SOL": {"USD": 195, "min": 0.5, "max": 1000},
    "XRP": {"USD": 2.35, "min": 50, "max": 50000},
    "DOGE": {"USD": 0.32, "min": 100, "max": 500000},
    "LTC": {"USD": 105, "min": 0.5, "max": 500},
    "TRX": {"USD": 0.26, "min": 100, "max": 500000},
    "MATIC": {"USD": 0.48, "min": 50, "max": 50000},
    "TON": {"USD": 5.8, "min": 10, "max": 10000},
    "AVAX": {"USD": 40, "min": 1, "max": 1000},
    "ADA": {"USD": 0.95, "min": 50, "max": 50000},
}


def get_mock_currencies() -> List[Currency]:
    """Get mock currencies list"""
    return [
        Currency(
            code=c["code"],
            coin=c["coin"],
            network=c["network"],
            name=c["name"],
            recv=c["recv"],
            send=c["send"],
            tag=c.get("tag"),
            logo=c["logo"],
            color=c["color"],
            priority=c["priority"]
        )
        for c in MOCK_CURRENCIES
    ]


def get_mock_exchange_rate(from_ccy: str, to_ccy: str, amount: float, direction: str) -> ExchangeRate:
    """Calculate mock exchange rate"""
    from_rate_data = MOCK_RATES.get(from_ccy, {"USD": 1.0, "min": 1, "max": 10000})
    to_rate_data = MOCK_RATES.get(to_ccy, {"USD": 1.0, "min": 1, "max": 10000})
    
    from_usd = from_rate_data["USD"]
    to_usd = to_rate_data["USD"]
    
    # Calculate exchange rate with 1.5% fee
    rate = (from_usd / to_usd) * 0.985
    
    if direction == "from":
        from_amount = amount
        to_amount = amount * rate
    else:
        to_amount = amount
        from_amount = amount / rate
    
    from_currency = CurrencyRate(
        code=from_ccy,
        network=from_ccy,
        coin=from_ccy,
        amount=f"{from_amount:.8f}",
        rate=f"{rate:.8f}",
        precision=8,
        min=str(from_rate_data["min"]),
        max=str(from_rate_data["max"]),
        usd=f"{from_amount * from_usd:.2f}",
        btc=f"{from_amount * from_usd / MOCK_RATES['BTC']['USD']:.8f}"
    )
    
    to_currency = CurrencyRate(
        code=to_ccy,
        network=to_ccy,
        coin=to_ccy,
        amount=f"{to_amount:.8f}",
        rate=f"{1/rate:.8f}",
        precision=8,
        min=str(to_rate_data["min"]),
        max=str(to_rate_data["max"]),
        usd=f"{to_amount * to_usd:.2f}",
        btc=f"{to_amount * to_usd / MOCK_RATES['BTC']['USD']:.8f}"
    )
    
    return ExchangeRate(
        from_rate=from_currency,
        to_rate=to_currency,
        errors=[]
    )


def create_mock_order(from_ccy: str, to_ccy: str, amount: float, direction: str, to_address: str, tag: str = None) -> Order:
    """Create mock order"""
    exchange_rate = get_mock_exchange_rate(from_ccy, to_ccy, amount, direction)
    
    order_id = f"MOCK{uuid.uuid4().hex[:8].upper()}"
    token = uuid.uuid4().hex
    current_time = int(time.time())
    
    # Generate mock deposit address
    mock_addresses = {
        "BTC": "bc1qmock" + uuid.uuid4().hex[:32],
        "ETH": "0xMock" + uuid.uuid4().hex[:40],
        "USDTTRC": "TMock" + uuid.uuid4().hex[:33],
        "USDTERC": "0xMock" + uuid.uuid4().hex[:40],
        "USDC": "0xMock" + uuid.uuid4().hex[:40],
        "BNB": "bnb1mock" + uuid.uuid4().hex[:38],
        "SOL": "Mock" + uuid.uuid4().hex[:43],
        "XRP": "rMock" + uuid.uuid4().hex[:33],
        "DOGE": "DMock" + uuid.uuid4().hex[:33],
        "LTC": "ltc1mock" + uuid.uuid4().hex[:32],
        "TRX": "TMock" + uuid.uuid4().hex[:33],
        "MATIC": "0xMock" + uuid.uuid4().hex[:40],
        "TON": "EQMock" + uuid.uuid4().hex[:46],
        "AVAX": "0xMock" + uuid.uuid4().hex[:40],
        "ADA": "addr1mock" + uuid.uuid4().hex[:50],
    }
    
    from_address = mock_addresses.get(from_ccy, "0xMock" + uuid.uuid4().hex[:40])
    
    return Order(
        id=order_id,
        type="fixed",
        email="",
        status=OrderStatus.NEW,
        time=TimeData(
            reg=current_time,
            start=None,
            finish=None,
            update=current_time,
            expiration=current_time + 1800,  # 30 minutes
            left=1800
        ),
        from_currency=OrderCurrency(
            code=from_ccy,
            coin=from_ccy,
            network=from_ccy,
            name=from_ccy,
            alias=from_ccy,
            amount=exchange_rate.from_rate.amount,
            address=from_address,
            addressAlt=None,
            tag=None,
            tagName=None,
            reqConfirmations=1,
            maxConfirmations=3,
            tx=Transaction()
        ),
        to_currency=OrderCurrency(
            code=to_ccy,
            coin=to_ccy,
            network=to_ccy,
            name=to_ccy,
            alias=to_ccy,
            amount=exchange_rate.to_rate.amount,
            address=to_address,
            addressAlt=None,
            tag=tag,
            tagName="Memo" if tag else None,
            reqConfirmations=1,
            maxConfirmations=3,
            tx=Transaction()
        ),
        back=None,
        emergency=Emergency(
            status=[],
            choice="NONE",
            repeat=False
        ),
        token=token
    )


# Mock orders storage (in-memory for dev mode)
MOCK_ORDERS: Dict[str, Order] = {}


def store_mock_order(order: Order):
    """Store mock order"""
    MOCK_ORDERS[order.id] = order


def get_mock_order(order_id: str, token: str) -> Order:
    """Get mock order by ID"""
    order = MOCK_ORDERS.get(order_id)
    if not order:
        raise ValueError(f"Order {order_id} not found")
    if order.token != token:
        raise ValueError("Invalid token")
    return order
