"""
Tests for fixedfloat_service.py - FixedFloat API integration service
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import (
    PriceRequest, CreateOrderRequest, OrderStatusRequest,
    EmergencyRequest, SetEmailRequest, QRRequest,
    ExchangeType, Direction, EmergencyChoice
)


class TestFixedFloatServiceInit:
    """Tests for FixedFloatService initialization"""
    
    def test_init_with_credentials(self):
        """Test initialization with API credentials"""
        with patch('fixedfloat_service.settings') as mock_settings:
            mock_settings.fixedfloat_api_key = "test_key"
            mock_settings.fixedfloat_api_secret = "test_secret"
            
            with patch('fixedfloat_service.FixedFloatApi') as mock_api:
                from fixedfloat_service import FixedFloatService
                service = FixedFloatService()
                
                assert service.api is not None
    
    def test_init_without_credentials(self):
        """Test initialization without API credentials"""
        with patch('fixedfloat_service.settings') as mock_settings:
            mock_settings.fixedfloat_api_key = None
            mock_settings.fixedfloat_api_secret = None
            
            with patch('fixedfloat_service.FixedFloatApi'):
                from fixedfloat_service import FixedFloatService
                service = FixedFloatService()
                
                assert service.api is None
    
    def test_xml_api_always_created(self):
        """Test that XML API is always created (no auth needed)"""
        with patch('fixedfloat_service.settings') as mock_settings:
            mock_settings.fixedfloat_api_key = None
            mock_settings.fixedfloat_api_secret = None
            
            with patch('fixedfloat_service.FixedFloatApi') as mock_api:
                from fixedfloat_service import FixedFloatService
                service = FixedFloatService()
                
                assert service.xml_api is not None


class TestEnsureApiConfigured:
    """Tests for _ensure_api_configured method"""
    
    def test_raises_when_not_configured(self):
        """Test that exception is raised when API not configured"""
        with patch('fixedfloat_service.settings') as mock_settings:
            mock_settings.fixedfloat_api_key = None
            mock_settings.fixedfloat_api_secret = None
            
            with patch('fixedfloat_service.FixedFloatApi'):
                from fixedfloat_service import FixedFloatService
                service = FixedFloatService()
                
                with pytest.raises(Exception) as exc_info:
                    service._ensure_api_configured()
                
                assert "credentials not configured" in str(exc_info.value)
    
    def test_passes_when_configured(self):
        """Test that no exception when API is configured"""
        with patch('fixedfloat_service.settings') as mock_settings:
            mock_settings.fixedfloat_api_key = "test_key"
            mock_settings.fixedfloat_api_secret = "test_secret"
            
            with patch('fixedfloat_service.FixedFloatApi'):
                from fixedfloat_service import FixedFloatService
                service = FixedFloatService()
                
                # Should not raise
                service._ensure_api_configured()


class TestGetCurrencies:
    """Tests for get_currencies method"""
    
    @pytest.fixture
    def mock_service(self):
        """Create service with mocked API"""
        with patch('fixedfloat_service.settings') as mock_settings:
            mock_settings.fixedfloat_api_key = "test_key"
            mock_settings.fixedfloat_api_secret = "test_secret"
            
            with patch('fixedfloat_service.FixedFloatApi') as mock_api_class:
                mock_api = MagicMock()
                mock_api_class.return_value = mock_api
                
                from fixedfloat_service import FixedFloatService
                service = FixedFloatService()
                service.api = mock_api
                
                yield service, mock_api
    
    @pytest.mark.asyncio
    async def test_get_currencies_success(self, mock_service):
        """Test successful currency retrieval"""
        service, mock_api = mock_service
        
        mock_api.ccies.return_value = [
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
            }
        ]
        
        currencies = await service.get_currencies()
        
        assert len(currencies) == 1
        assert currencies[0].code == "BTC"
        assert currencies[0].name == "Bitcoin"
    
    @pytest.mark.asyncio
    async def test_get_currencies_api_error(self, mock_service):
        """Test currency retrieval with API error"""
        service, mock_api = mock_service
        
        mock_api.ccies.side_effect = Exception("API Error")
        
        with pytest.raises(Exception) as exc_info:
            await service.get_currencies()
        
        assert "Failed to get currencies" in str(exc_info.value)


class TestGetExchangeRate:
    """Tests for get_exchange_rate method"""
    
    @pytest.fixture
    def mock_service(self):
        """Create service with mocked API"""
        with patch('fixedfloat_service.settings') as mock_settings:
            mock_settings.fixedfloat_api_key = "test_key"
            mock_settings.fixedfloat_api_secret = "test_secret"
            
            with patch('fixedfloat_service.FixedFloatApi') as mock_api_class:
                mock_api = MagicMock()
                mock_api_class.return_value = mock_api
                
                from fixedfloat_service import FixedFloatService
                service = FixedFloatService()
                service.api = mock_api
                
                yield service, mock_api
    
    @pytest.fixture
    def price_request(self):
        """Create sample price request"""
        return PriceRequest(
            type=ExchangeType.FIXED,
            fromCcy="BTC",
            toCcy="ETH",
            direction=Direction.FROM,
            amount=0.1
        )
    
    @pytest.mark.asyncio
    async def test_get_exchange_rate_success(self, mock_service, price_request):
        """Test successful exchange rate retrieval"""
        service, mock_api = mock_service
        
        mock_api.price.return_value = {
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
        }
        
        rate = await service.get_exchange_rate(price_request)
        
        assert rate.from_rate.code == "BTC"
        assert rate.to_rate.code == "ETH"
        assert rate.to_rate.amount == "2.95"
    
    @pytest.mark.asyncio
    async def test_get_exchange_rate_api_error(self, mock_service, price_request):
        """Test exchange rate retrieval with API error"""
        service, mock_api = mock_service
        
        mock_api.price.side_effect = Exception("API Error")
        
        with pytest.raises(Exception) as exc_info:
            await service.get_exchange_rate(price_request)
        
        assert "Failed to get exchange rate" in str(exc_info.value)


class TestCreateOrder:
    """Tests for create_order method"""
    
    @pytest.fixture
    def mock_service(self):
        """Create service with mocked API"""
        with patch('fixedfloat_service.settings') as mock_settings:
            mock_settings.fixedfloat_api_key = "test_key"
            mock_settings.fixedfloat_api_secret = "test_secret"
            
            with patch('fixedfloat_service.FixedFloatApi') as mock_api_class:
                mock_api = MagicMock()
                mock_api_class.return_value = mock_api
                
                from fixedfloat_service import FixedFloatService
                service = FixedFloatService()
                service.api = mock_api
                
                yield service, mock_api
    
    @pytest.fixture
    def create_request(self):
        """Create sample create order request"""
        return CreateOrderRequest(
            type=ExchangeType.FIXED,
            fromCcy="BTC",
            toCcy="ETH",
            direction=Direction.FROM,
            amount=0.1,
            toAddress="0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6"
        )
    
    @pytest.fixture
    def order_response(self):
        """Sample order response from API"""
        return {
            "id": "ORDER123",
            "type": "fixed",
            "email": "",
            "status": "NEW",
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
                "address": "0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6",
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
                "choice": "NONE",
                "repeat": False
            }
        }
    
    @pytest.mark.asyncio
    async def test_create_order_success(self, mock_service, create_request, order_response):
        """Test successful order creation"""
        service, mock_api = mock_service
        
        mock_api.create.return_value = order_response
        
        order = await service.create_order(create_request)
        
        assert order.id == "ORDER123"
        assert order.token == "token123"
    
    @pytest.mark.asyncio
    async def test_create_order_api_error(self, mock_service, create_request):
        """Test order creation with API error"""
        service, mock_api = mock_service
        
        mock_api.create.side_effect = Exception("API Error")
        
        with pytest.raises(Exception) as exc_info:
            await service.create_order(create_request)
        
        assert "Failed to create order" in str(exc_info.value)


class TestGetOrderStatus:
    """Tests for get_order_status method"""
    
    @pytest.fixture
    def mock_service(self):
        """Create service with mocked API"""
        with patch('fixedfloat_service.settings') as mock_settings:
            mock_settings.fixedfloat_api_key = "test_key"
            mock_settings.fixedfloat_api_secret = "test_secret"
            
            with patch('fixedfloat_service.FixedFloatApi') as mock_api_class:
                mock_api = MagicMock()
                mock_api_class.return_value = mock_api
                
                from fixedfloat_service import FixedFloatService
                service = FixedFloatService()
                service.api = mock_api
                
                yield service, mock_api
    
    @pytest.fixture
    def order_request(self):
        """Create sample order status request"""
        return OrderStatusRequest(
            id="ORDER123",
            token="token123"
        )
    
    @pytest.mark.asyncio
    async def test_get_order_status_api_error(self, mock_service, order_request):
        """Test order status retrieval with API error"""
        service, mock_api = mock_service
        
        mock_api.order.side_effect = Exception("API Error")
        
        with pytest.raises(Exception) as exc_info:
            await service.get_order_status(order_request)
        
        assert "Failed to get order status" in str(exc_info.value)


class TestHandleEmergency:
    """Tests for handle_emergency method"""
    
    @pytest.fixture
    def mock_service(self):
        """Create service with mocked API"""
        with patch('fixedfloat_service.settings') as mock_settings:
            mock_settings.fixedfloat_api_key = "test_key"
            mock_settings.fixedfloat_api_secret = "test_secret"
            
            with patch('fixedfloat_service.FixedFloatApi') as mock_api_class:
                mock_api = MagicMock()
                mock_api_class.return_value = mock_api
                
                from fixedfloat_service import FixedFloatService
                service = FixedFloatService()
                service.api = mock_api
                
                yield service, mock_api
    
    @pytest.fixture
    def emergency_request(self):
        """Create sample emergency request"""
        return EmergencyRequest(
            id="ORDER123",
            token="token123",
            choice=EmergencyChoice.EXCHANGE
        )
    
    @pytest.mark.asyncio
    async def test_handle_emergency_success(self, mock_service, emergency_request):
        """Test successful emergency handling"""
        service, mock_api = mock_service
        
        mock_api.emergency.return_value = {
            "status": "processed",
            "message": "Emergency action completed"
        }
        
        response = await service.handle_emergency(emergency_request)
        
        assert response.id == "ORDER123"
        assert response.choice == EmergencyChoice.EXCHANGE
        assert response.status == "processed"
    
    @pytest.mark.asyncio
    async def test_handle_emergency_api_error(self, mock_service, emergency_request):
        """Test emergency handling with API error"""
        service, mock_api = mock_service
        
        mock_api.emergency.side_effect = Exception("API Error")
        
        with pytest.raises(Exception) as exc_info:
            await service.handle_emergency(emergency_request)
        
        assert "Failed to handle emergency" in str(exc_info.value)


class TestSetEmail:
    """Tests for set_email method"""
    
    @pytest.fixture
    def mock_service(self):
        """Create service with mocked API"""
        with patch('fixedfloat_service.settings') as mock_settings:
            mock_settings.fixedfloat_api_key = "test_key"
            mock_settings.fixedfloat_api_secret = "test_secret"
            
            with patch('fixedfloat_service.FixedFloatApi') as mock_api_class:
                mock_api = MagicMock()
                mock_api_class.return_value = mock_api
                
                from fixedfloat_service import FixedFloatService
                service = FixedFloatService()
                service.api = mock_api
                
                yield service, mock_api
    
    @pytest.fixture
    def email_request(self):
        """Create sample email request"""
        return SetEmailRequest(
            id="ORDER123",
            token="token123",
            email="test@example.com"
        )
    
    @pytest.mark.asyncio
    async def test_set_email_success(self, mock_service, email_request):
        """Test successful email setting"""
        service, mock_api = mock_service
        
        mock_api.setEmail.return_value = {
            "status": "email_set"
        }
        
        response = await service.set_email(email_request)
        
        assert response.id == "ORDER123"
        assert response.email == "test@example.com"
        assert response.status == "email_set"
    
    @pytest.mark.asyncio
    async def test_set_email_api_error(self, mock_service, email_request):
        """Test email setting with API error"""
        service, mock_api = mock_service
        
        mock_api.setEmail.side_effect = Exception("API Error")
        
        with pytest.raises(Exception) as exc_info:
            await service.set_email(email_request)
        
        assert "Failed to set email" in str(exc_info.value)


class TestGetQRCodes:
    """Tests for get_qr_codes method"""
    
    @pytest.fixture
    def mock_service(self):
        """Create service with mocked API"""
        with patch('fixedfloat_service.settings') as mock_settings:
            mock_settings.fixedfloat_api_key = "test_key"
            mock_settings.fixedfloat_api_secret = "test_secret"
            
            with patch('fixedfloat_service.FixedFloatApi') as mock_api_class:
                mock_api = MagicMock()
                mock_api_class.return_value = mock_api
                
                from fixedfloat_service import FixedFloatService
                service = FixedFloatService()
                service.api = mock_api
                
                yield service, mock_api
    
    @pytest.fixture
    def qr_request(self):
        """Create sample QR request"""
        return QRRequest(
            id="ORDER123",
            token="token123"
        )
    
    @pytest.mark.asyncio
    async def test_get_qr_codes_api_error(self, mock_service, qr_request):
        """Test QR code retrieval with API error"""
        service, mock_api = mock_service
        
        mock_api.qr.side_effect = Exception("API Error")
        
        with pytest.raises(Exception) as exc_info:
            await service.get_qr_codes(qr_request)
        
        assert "Failed to get QR codes" in str(exc_info.value)


class TestXMLRates:
    """Tests for XML rates methods"""
    
    @pytest.fixture
    def mock_service(self):
        """Create service with mocked XML API"""
        with patch('fixedfloat_service.settings') as mock_settings:
            mock_settings.fixedfloat_api_key = None
            mock_settings.fixedfloat_api_secret = None
            
            with patch('fixedfloat_service.FixedFloatApi') as mock_api_class:
                mock_xml_api = MagicMock()
                mock_api_class.return_value = mock_xml_api
                
                from fixedfloat_service import FixedFloatService
                service = FixedFloatService()
                service.xml_api = mock_xml_api
                
                yield service, mock_xml_api
    
    @pytest.mark.asyncio
    async def test_get_fixed_rates_xml_raw(self, mock_service):
        """Test getting raw fixed rates XML"""
        service, mock_xml_api = mock_service
        
        mock_xml_api.get_rates_fixed_xml.return_value = "<rates><rate/></rates>"
        
        result = await service.get_fixed_rates_xml(parse=False)
        
        assert result == "<rates><rate/></rates>"
    
    @pytest.mark.asyncio
    async def test_get_fixed_rates_xml_parsed(self, mock_service):
        """Test getting parsed fixed rates"""
        service, mock_xml_api = mock_service
        
        mock_xml_api.get_rates_fixed_xml.return_value = [
            {"from": "BTC", "to": "ETH", "in": 1.0, "out": 29.5}
        ]
        
        result = await service.get_fixed_rates_xml(parse=True)
        
        assert isinstance(result, list)
        assert len(result) == 1
    
    @pytest.mark.asyncio
    async def test_get_float_rates_xml_raw(self, mock_service):
        """Test getting raw float rates XML"""
        service, mock_xml_api = mock_service
        
        mock_xml_api.get_rates_float_xml.return_value = "<rates><rate/></rates>"
        
        result = await service.get_float_rates_xml(parse=False)
        
        assert result == "<rates><rate/></rates>"
    
    @pytest.mark.asyncio
    async def test_get_float_rates_xml_parsed(self, mock_service):
        """Test getting parsed float rates"""
        service, mock_xml_api = mock_service
        
        mock_xml_api.get_rates_float_xml.return_value = [
            {"from": "BTC", "to": "ETH", "in": 1.0, "out": 29.8}
        ]
        
        result = await service.get_float_rates_xml(parse=True)
        
        assert isinstance(result, list)
        assert len(result) == 1
