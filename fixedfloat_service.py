import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../FixedFloatApi-Python'))

from fixedfloatapi import FixedFloatApi
from typing import Dict, Any, Optional, List
import httpx
import xml.etree.ElementTree as ET
from config import settings
from models import *
from partner_system import partner_system

class FixedFloatService:
    """Service for interacting with FixedFloat API"""
    
    def __init__(self):
        self.api = None
        if settings.fixedfloat_api_key and settings.fixedfloat_api_secret:
            self.api = FixedFloatApi(
                key=settings.fixedfloat_api_key,
                secret=settings.fixedfloat_api_secret
            )
        
        # For XML endpoints, we don't need authentication
        self.xml_api = FixedFloatApi(key=None, secret=None)
    
    def _ensure_api_configured(self):
        """Ensure API is configured with credentials"""
        if not self.api:
            raise Exception("FixedFloat API credentials not configured")
    
    async def get_currencies(self) -> List[Currency]:
        """Get list of supported currencies"""
        self._ensure_api_configured()
        
        try:
            data = self.api.ccies()
            currencies = []
            
            # Convert FixedFloat response to our Currency model
            for currency_data in data:
                currency = Currency(
                    code=currency_data.get('code', ''),
                    coin=currency_data.get('coin', ''),
                    network=currency_data.get('network', ''),
                    name=currency_data.get('name', ''),
                    recv=currency_data.get('recv', False),
                    send=currency_data.get('send', False),
                    tag=currency_data.get('tag'),
                    logo=currency_data.get('logo', ''),
                    color=currency_data.get('color', ''),
                    priority=currency_data.get('priority', 0)
                )
                currencies.append(currency)
            
            return currencies
            
        except Exception as e:
            raise Exception(f"Failed to get currencies: {str(e)}")
    
    async def get_exchange_rate(self, request: PriceRequest) -> ExchangeRate:
        """Get exchange rate for currency pair"""
        self._ensure_api_configured()
        
        try:
            # Prepare request data
            request_data = {
                'type': request.type.value,
                'fromCcy': request.fromCcy,
                'toCcy': request.toCcy,
                'direction': request.direction.value,
                'amount': request.amount
            }
            
            # Add optional parameters
            if request.ccies:
                request_data['ccies'] = request.ccies
            if request.usd:
                request_data['usd'] = request.usd
            if request.refcode:
                request_data['refcode'] = request.refcode
            if request.afftax:
                request_data['afftax'] = request.afftax
            
            data = self.api.price(request_data)
            
            # Convert response to our ExchangeRate model
            from_rate = CurrencyRate(
                code=data['from']['code'],
                network=data['from']['network'],
                coin=data['from']['coin'],
                amount=str(data['from']['amount']),
                rate=str(data['from']['rate']),
                precision=data['from']['precision'],
                min=str(data['from']['min']),
                max=str(data['from']['max']),
                usd=str(data['from']['usd']),
                btc=str(data['from'].get('btc', ''))
            )
            
            to_rate = CurrencyRate(
                code=data['to']['code'],
                network=data['to']['network'],
                coin=data['to']['coin'],
                amount=str(data['to']['amount']),
                rate=str(data['to']['rate']),
                precision=data['to']['precision'],
                min=str(data['to']['min']),
                max=str(data['to']['max']),
                usd=str(data['to']['usd']),
                btc=str(data['to'].get('btc', ''))
            )
            
            # Get currencies list if requested
            currencies = None
            if request.ccies and 'ccies' in data:
                currencies = []
                for currency_data in data['ccies']:
                    currency = Currency(
                        code=currency_data.get('code', ''),
                        coin=currency_data.get('coin', ''),
                        network=currency_data.get('network', ''),
                        name=currency_data.get('name', ''),
                        recv=currency_data.get('recv', False),
                        send=currency_data.get('send', False),
                        tag=currency_data.get('tag'),
                        logo=currency_data.get('logo', ''),
                        color=currency_data.get('color', ''),
                        priority=currency_data.get('priority', 0)
                    )
                    currencies.append(currency)
            
            return ExchangeRate(
                from_rate=from_rate,
                to_rate=to_rate,
                errors=data.get('errors', []),
                ccies=currencies
            )
            
        except Exception as e:
            raise Exception(f"Failed to get exchange rate: {str(e)}")
    
    async def create_order(self, request: CreateOrderRequest) -> Order:
        """Create new exchange order"""
        self._ensure_api_configured()
        
        try:
            # Prepare request data
            request_data = {
                'type': request.type.value,
                'fromCcy': request.fromCcy,
                'toCcy': request.toCcy,
                'direction': request.direction.value,
                'amount': request.amount,
                'toAddress': request.toAddress
            }
            
            # Add optional parameters
            if request.tag:
                request_data['tag'] = request.tag
            if request.refcode:
                request_data['refcode'] = request.refcode
            if request.afftax:
                request_data['afftax'] = request.afftax
            
            data = self.api.create(request_data)
            
            # Convert response to our Order model
            order = self._convert_order_data(data)
            return order
            
        except Exception as e:
            raise Exception(f"Failed to create order: {str(e)}")
    
    async def get_order_status(self, request: OrderStatusRequest) -> Order:
        """Get order status"""
        self._ensure_api_configured()
        
        try:
            request_data = {
                'id': request.id,
                'token': request.token
            }
            
            data = self.api.order(request_data)
            order = self._convert_order_data(data)
            return order
            
        except Exception as e:
            raise Exception(f"Failed to get order status: {str(e)}")
    
    async def handle_emergency(self, request: EmergencyRequest) -> EmergencyResponse:
        """Handle emergency situation"""
        self._ensure_api_configured()
        
        try:
            request_data = {
                'id': request.id,
                'token': request.token,
                'choice': request.choice.value
            }
            
            if request.address:
                request_data['address'] = request.address
            if request.tag:
                request_data['tag'] = request.tag
            
            data = self.api.emergency(request_data)
            
            return EmergencyResponse(
                id=request.id,
                choice=request.choice,
                status=data.get('status', 'processed'),
                message=data.get('message', 'Emergency action processed')
            )
            
        except Exception as e:
            raise Exception(f"Failed to handle emergency: {str(e)}")
    
    async def set_email(self, request: SetEmailRequest) -> SetEmailResponse:
        """Set email for order notifications"""
        self._ensure_api_configured()
        
        try:
            request_data = {
                'id': request.id,
                'token': request.token,
                'email': request.email
            }
            
            data = self.api.setEmail(request_data)
            
            return SetEmailResponse(
                id=request.id,
                email=request.email,
                status=data.get('status', 'email_set')
            )
            
        except Exception as e:
            raise Exception(f"Failed to set email: {str(e)}")
    
    async def get_qr_codes(self, request: QRRequest) -> QRResponse:
        """Get QR codes for order"""
        self._ensure_api_configured()
        
        try:
            request_data = {
                'id': request.id,
                'token': request.token
            }
            
            data = self.api.qr(request_data)
            
            qr_codes = []
            for qr_data in data:
                qr_code = QRCode(
                    title=qr_data.get('title', ''),
                    src=qr_data.get('src', ''),
                    checked=qr_data.get('checked', False)
                )
                qr_codes.append(qr_code)
            
            return QRResponse(qr_codes=qr_codes)
            
        except Exception as e:
            raise Exception(f"Failed to get QR codes: {str(e)}")
    
    async def get_fixed_rates_xml(self, parse: bool = True) -> List[XMLRate]:
        """Get fixed exchange rates from XML endpoint"""
        try:
            if parse:
                rates_data = self.xml_api.get_rates_fixed_xml(parse=True)
                xml_rates = []
                
                for rate_data in rates_data:
                    xml_rate = XMLRate(
                        **{
                            'from': rate_data.get('from', ''),
                            'to': rate_data.get('to', ''),
                            'in': rate_data.get('in', 0.0),
                            'out': rate_data.get('out', 0.0),
                            'amount': rate_data.get('amount', 0.0),
                            'tofee': rate_data.get('tofee'),
                            'minamount': rate_data.get('minamount'),
                            'maxamount': rate_data.get('maxamount')
                        }
                    )
                    xml_rates.append(xml_rate)
                
                return xml_rates
            else:
                # Return raw XML
                return self.xml_api.get_rates_fixed_xml(parse=False)
                
        except Exception as e:
            raise Exception(f"Failed to get fixed rates XML: {str(e)}")
    
    async def get_float_rates_xml(self, parse: bool = True) -> List[XMLRate]:
        """Get floating exchange rates from XML endpoint"""
        try:
            if parse:
                rates_data = self.xml_api.get_rates_float_xml(parse=True)
                xml_rates = []
                
                for rate_data in rates_data:
                    xml_rate = XMLRate(
                        **{
                            'from': rate_data.get('from', ''),
                            'to': rate_data.get('to', ''),
                            'in': rate_data.get('in', 0.0),
                            'out': rate_data.get('out', 0.0),
                            'amount': rate_data.get('amount', 0.0),
                            'tofee': rate_data.get('tofee'),
                            'minamount': rate_data.get('minamount'),
                            'maxamount': rate_data.get('maxamount')
                        }
                    )
                    xml_rates.append(xml_rate)
                
                return xml_rates
            else:
                # Return raw XML
                return self.xml_api.get_rates_float_xml(parse=False)
                
        except Exception as e:
            raise Exception(f"Failed to get float rates XML: {str(e)}")
    
    def _convert_order_data(self, data: Dict[str, Any]) -> Order:
        """Convert FixedFloat order data to our Order model"""
        # Create transaction objects
        from_tx = Transaction(
            id=data['from']['tx'].get('id'),
            amount=data['from']['tx'].get('amount'),
            fee=data['from']['tx'].get('fee'),
            ccyfee=data['from']['tx'].get('ccyfee'),
            timeReg=data['from']['tx'].get('timeReg'),
            timeBlock=data['from']['tx'].get('timeBlock'),
            confirmations=data['from']['tx'].get('confirmations')
        )
        
        to_tx = Transaction(
            id=data['to']['tx'].get('id'),
            amount=data['to']['tx'].get('amount'),
            fee=data['to']['tx'].get('fee'),
            ccyfee=data['to']['tx'].get('ccyfee'),
            timeReg=data['to']['tx'].get('timeReg'),
            timeBlock=data['to']['tx'].get('timeBlock'),
            confirmations=data['to']['tx'].get('confirmations')
        )
        
        # Create currency objects
        from_currency = OrderCurrency(
            code=data['from']['code'],
            coin=data['from']['coin'],
            network=data['from']['network'],
            name=data['from']['name'],
            alias=data['from']['alias'],
            amount=data['from']['amount'],
            address=data['from']['address'],
            addressAlt=data['from'].get('addressAlt'),
            tag=data['from'].get('tag'),
            tagName=data['from'].get('tagName'),
            reqConfirmations=data['from']['reqConfirmations'],
            maxConfirmations=data['from']['maxConfirmations'],
            tx=from_tx
        )
        
        to_currency = OrderCurrency(
            code=data['to']['code'],
            coin=data['to']['coin'],
            network=data['to']['network'],
            name=data['to']['name'],
            alias=data['to']['alias'],
            amount=data['to']['amount'],
            address=data['to']['address'],
            addressAlt=data['to'].get('addressAlt'),
            tag=data['to'].get('tag'),
            tagName=data['to'].get('tagName'),
            reqConfirmations=data['to']['reqConfirmations'],
            maxConfirmations=data['to']['maxConfirmations'],
            tx=to_tx
        )
        
        # Create time data
        time_data = TimeData(
            reg=data['time']['reg'],
            start=data['time'].get('start'),
            finish=data['time'].get('finish'),
            update=data['time']['update'],
            expiration=data['time']['expiration'],
            left=data['time']['left']
        )
        
        # Create emergency data
        emergency = Emergency(
            status=data['emergency']['status'],
            choice=data['emergency']['choice'],
            repeat=data['emergency']['repeat']
        )
        
        # Handle back currency if exists
        back_currency = None
        if 'back' in data and data['back']:
            back_tx = Transaction(
                id=data['back']['tx'].get('id'),
                amount=data['back']['tx'].get('amount'),
                fee=data['back']['tx'].get('fee'),
                ccyfee=data['back']['tx'].get('ccyfee'),
                timeReg=data['back']['tx'].get('timeReg'),
                timeBlock=data['back']['tx'].get('timeBlock'),
                confirmations=data['back']['tx'].get('confirmations')
            )
            
            back_currency = OrderCurrency(
                code=data['back']['code'],
                coin=data['back']['coin'],
                network=data['back']['network'],
                name=data['back']['name'],
                alias=data['back']['alias'],
                amount=data['back']['amount'],
                address=data['back']['address'],
                addressAlt=data['back'].get('addressAlt'),
                tag=data['back'].get('tag'),
                tagName=data['back'].get('tagName'),
                reqConfirmations=data['back']['reqConfirmations'],
                maxConfirmations=data['back']['maxConfirmations'],
                tx=back_tx
            )
        
        return Order(
            id=data['id'],
            type=data['type'],
            email=data['email'],
            status=OrderStatus(data['status']),
            time=time_data,
            from_currency=from_currency,
            to_currency=to_currency,
            back=back_currency,
            emergency=emergency,
            token=data['token']
        )

# Global service instance
fixedfloat_service = FixedFloatService()