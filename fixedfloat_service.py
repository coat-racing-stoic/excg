import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../FixedFloatApi-Python'))

from fixedfloatapi import FixedFloatApi
from typing import Dict, Any, Optional, List, Union
import httpx
import xml.etree.ElementTree as ET
from config import settings
from models import *
from partner_system import partner_system
from logging_config import get_logger

class FixedFloatService:
    """Service for interacting with FixedFloat API"""
    
    def __init__(self):
        self.logger = get_logger('fixedfloat')
        self.api = None
        if settings.fixedfloat_api_key and settings.fixedfloat_api_secret:
            self.api = FixedFloatApi(
                key=settings.fixedfloat_api_key,
                secret=settings.fixedfloat_api_secret,
                logger=self.logger
            )
            self.logger.info(
                "FixedFloat API initialized with credentials",
                extra={'event_type': 'service_init', 'has_credentials': True}
            )
        else:
            self.logger.warning(
                "FixedFloat API initialized without credentials",
                extra={'event_type': 'service_init', 'has_credentials': False}
            )
        
        # For XML endpoints, we don't need authentication
        self.xml_api = FixedFloatApi(key=None, secret=None, logger=self.logger)
        
        # Кэш курсов (ленивая инициализация)
        self._rates_cache = None
        
        # Валидатор валют (ленивая инициализация)
        self._currency_validator = None
    
    @property
    def rates_cache(self):
        """Ленивая инициализация кэша курсов"""
        if self._rates_cache is None:
            from redis_cache import rates_cache
            self._rates_cache = rates_cache
        return self._rates_cache
    
    @property
    def currency_validator(self):
        """Ленивая инициализация валидатора валют"""
        if self._currency_validator is None:
            from currency_validator import currency_validator
            self._currency_validator = currency_validator
        return self._currency_validator
    
    def _ensure_api_configured(self):
        """Ensure API is configured with credentials"""
        if not self.api:
            self.logger.error(
                "API call attempted without credentials",
                extra={'event_type': 'api_error', 'error': 'no_credentials'}
            )
            raise Exception("FixedFloat API credentials not configured")
    
    async def _validate_currency_pair(self, from_ccy: str, to_ccy: str):
        """Валидация пары валют перед операцией"""
        is_valid, error_msg = await self.currency_validator.validate_pair(from_ccy, to_ccy)
        if not is_valid:
            self.logger.warning(
                f"Currency pair validation failed: {error_msg}",
                extra={
                    'event_type': 'validation_error',
                    'from_ccy': from_ccy,
                    'to_ccy': to_ccy,
                    'error': error_msg
                }
            )
            raise ValueError(error_msg)
        return True
    
    async def get_currencies(self) -> List[Currency]:
        """Get list of supported currencies"""
        self._ensure_api_configured()
        
        self.logger.info(
            "Fetching currencies list",
            extra={'event_type': 'api_call', 'method': 'ccies'}
        )
        
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
            
            # Обновляем кэш валидатора валют (TTL 1 час)
            await self.currency_validator.update_currencies(data)
            
            self.logger.info(
                f"Fetched {len(currencies)} currencies",
                extra={'event_type': 'api_response', 'method': 'ccies', 'count': len(currencies)}
            )
            
            return currencies
            
        except Exception as e:
            self.logger.error(
                f"Failed to get currencies: {str(e)}",
                extra={'event_type': 'api_error', 'method': 'ccies', 'error': str(e)}
            )
            raise Exception(f"Failed to get currencies: {str(e)}")
    
    async def get_exchange_rate(self, request: PriceRequest) -> ExchangeRate:
        """Get exchange rate for currency pair"""
        self._ensure_api_configured()
        
        # Валидация пары валют
        await self._validate_currency_pair(request.fromCcy, request.toCcy)
        
        self.logger.info(
            f"Getting exchange rate {request.fromCcy}->{request.toCcy}",
            extra={
                'event_type': 'api_call',
                'method': 'price',
                'from_ccy': request.fromCcy,
                'to_ccy': request.toCcy,
                'amount': request.amount,
                'type': request.type.value
            }
        )
        
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
            
            self.logger.info(
                f"Exchange rate fetched: {request.fromCcy}->{request.toCcy}",
                extra={
                    'event_type': 'api_response',
                    'method': 'price',
                    'from_ccy': request.fromCcy,
                    'to_ccy': request.toCcy,
                    'from_amount': from_rate.amount,
                    'to_amount': to_rate.amount
                }
            )
            
            return ExchangeRate(
                from_rate=from_rate,
                to_rate=to_rate,
                errors=data.get('errors', []),
                ccies=currencies
            )
            
        except Exception as e:
            self.logger.error(
                f"Failed to get exchange rate: {str(e)}",
                extra={
                    'event_type': 'api_error',
                    'method': 'price',
                    'from_ccy': request.fromCcy,
                    'to_ccy': request.toCcy,
                    'error': str(e)
                }
            )
            raise Exception(f"Failed to get exchange rate: {str(e)}")
    
    async def create_order(self, request: CreateOrderRequest) -> Order:
        """Create new exchange order"""
        self._ensure_api_configured()
        
        # Валидация пары валют
        await self._validate_currency_pair(request.fromCcy, request.toCcy)
        
        self.logger.info(
            f"Creating order {request.fromCcy}->{request.toCcy}",
            extra={
                'event_type': 'api_call',
                'method': 'create',
                'from_ccy': request.fromCcy,
                'to_ccy': request.toCcy,
                'amount': request.amount,
                'type': request.type.value
            }
        )
        
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
            
            self.logger.info(
                f"Order created: {order.id}",
                extra={
                    'event_type': 'order_created',
                    'method': 'create',
                    'order_id': order.id,
                    'from_ccy': request.fromCcy,
                    'to_ccy': request.toCcy,
                    'status': order.status.value
                }
            )
            
            return order
            
        except Exception as e:
            self.logger.error(
                f"Failed to create order: {str(e)}",
                extra={
                    'event_type': 'api_error',
                    'method': 'create',
                    'from_ccy': request.fromCcy,
                    'to_ccy': request.toCcy,
                    'error': str(e)
                }
            )
            raise Exception(f"Failed to create order: {str(e)}")
    
    async def get_order_status(self, request: OrderStatusRequest) -> Order:
        """Get order status"""
        self._ensure_api_configured()
        
        self.logger.info(
            f"Getting order status: {request.id}",
            extra={
                'event_type': 'api_call',
                'method': 'order',
                'order_id': request.id
            }
        )
        
        try:
            request_data = {
                'id': request.id,
                'token': request.token
            }
            
            data = self.api.order(request_data)
            order = self._convert_order_data(data)
            
            self.logger.info(
                f"Order status fetched: {order.id} - {order.status.value}",
                extra={
                    'event_type': 'api_response',
                    'method': 'order',
                    'order_id': order.id,
                    'status': order.status.value
                }
            )
            
            return order
            
        except Exception as e:
            self.logger.error(
                f"Failed to get order status: {str(e)}",
                extra={
                    'event_type': 'api_error',
                    'method': 'order',
                    'order_id': request.id,
                    'error': str(e)
                }
            )
            raise Exception(f"Failed to get order status: {str(e)}")
    
    async def handle_emergency(self, request: EmergencyRequest) -> EmergencyResponse:
        """Handle emergency situation"""
        self._ensure_api_configured()
        
        self.logger.warning(
            f"Handling emergency for order: {request.id}",
            extra={
                'event_type': 'api_call',
                'method': 'emergency',
                'order_id': request.id,
                'choice': request.choice.value
            }
        )
        
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
            
            self.logger.info(
                f"Emergency handled for order: {request.id}",
                extra={
                    'event_type': 'emergency_handled',
                    'method': 'emergency',
                    'order_id': request.id,
                    'choice': request.choice.value,
                    'status': data.get('status', 'processed')
                }
            )
            
            return EmergencyResponse(
                id=request.id,
                choice=request.choice,
                status=data.get('status', 'processed'),
                message=data.get('message', 'Emergency action processed')
            )
            
        except Exception as e:
            self.logger.error(
                f"Failed to handle emergency: {str(e)}",
                extra={
                    'event_type': 'api_error',
                    'method': 'emergency',
                    'order_id': request.id,
                    'error': str(e)
                }
            )
            raise Exception(f"Failed to handle emergency: {str(e)}")
    
    async def set_email(self, request: SetEmailRequest) -> SetEmailResponse:
        """Set email for order notifications"""
        self._ensure_api_configured()
        
        self.logger.info(
            f"Setting email for order: {request.id}",
            extra={
                'event_type': 'api_call',
                'method': 'setEmail',
                'order_id': request.id
            }
        )
        
        try:
            request_data = {
                'id': request.id,
                'token': request.token,
                'email': request.email
            }
            
            data = self.api.setEmail(request_data)
            
            self.logger.info(
                f"Email set for order: {request.id}",
                extra={
                    'event_type': 'api_response',
                    'method': 'setEmail',
                    'order_id': request.id,
                    'status': data.get('status', 'email_set')
                }
            )
            
            return SetEmailResponse(
                id=request.id,
                email=request.email,
                status=data.get('status', 'email_set')
            )
            
        except Exception as e:
            self.logger.error(
                f"Failed to set email: {str(e)}",
                extra={
                    'event_type': 'api_error',
                    'method': 'setEmail',
                    'order_id': request.id,
                    'error': str(e)
                }
            )
            raise Exception(f"Failed to set email: {str(e)}")
    
    async def get_qr_codes(self, request: QRRequest) -> QRResponse:
        """Get QR codes for order"""
        self._ensure_api_configured()
        
        self.logger.info(
            f"Getting QR codes for order: {request.id}",
            extra={
                'event_type': 'api_call',
                'method': 'qr',
                'order_id': request.id
            }
        )
        
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
            
            self.logger.info(
                f"QR codes fetched for order: {request.id}",
                extra={
                    'event_type': 'api_response',
                    'method': 'qr',
                    'order_id': request.id,
                    'qr_count': len(qr_codes)
                }
            )
            
            return QRResponse(qr_codes=qr_codes)
            
        except Exception as e:
            self.logger.error(
                f"Failed to get QR codes: {str(e)}",
                extra={
                    'event_type': 'api_error',
                    'method': 'qr',
                    'order_id': request.id,
                    'error': str(e)
                }
            )
            raise Exception(f"Failed to get QR codes: {str(e)}")
    
    async def get_fixed_rates_xml(self, parse: bool = True, use_cache: bool = True) -> Union[List[XMLRate], str]:
        """
        Get fixed exchange rates from XML endpoint
        
        Args:
            parse: If True, return parsed XMLRate objects. If False, return raw XML string.
            use_cache: If True, try to get rates from Redis cache first.
            
        Returns:
            List of XMLRate objects or raw XML string
        """
        try:
            # Пробуем получить из кэша (только для parsed данных)
            if parse and use_cache and settings.rates_cache_enabled:
                try:
                    cached_rates = await self.rates_cache.get_fixed_rates()
                    if cached_rates:
                        self.logger.debug(
                            f"Returning {len(cached_rates)} fixed rates from cache",
                            extra={'event_type': 'cache_hit', 'cache_type': 'fixed'}
                        )
                        return self._convert_rates_to_xml_models(cached_rates)
                except Exception as cache_error:
                    self.logger.warning(
                        f"Cache error, falling back to API: {cache_error}",
                        extra={'event_type': 'cache_fallback', 'error': str(cache_error)}
                    )
            
            # Получаем из API
            if parse:
                rates_data = self.xml_api.get_rates_fixed_xml(parse=True)
                return self._convert_rates_to_xml_models(rates_data)
            else:
                # Return raw XML
                return self.xml_api.get_rates_fixed_xml(parse=False)
                
        except Exception as e:
            raise Exception(f"Failed to get fixed rates XML: {str(e)}")
    
    async def get_float_rates_xml(self, parse: bool = True, use_cache: bool = True) -> Union[List[XMLRate], str]:
        """
        Get floating exchange rates from XML endpoint
        
        Args:
            parse: If True, return parsed XMLRate objects. If False, return raw XML string.
            use_cache: If True, try to get rates from Redis cache first.
            
        Returns:
            List of XMLRate objects or raw XML string
        """
        try:
            # Пробуем получить из кэша (только для parsed данных)
            if parse and use_cache and settings.rates_cache_enabled:
                try:
                    cached_rates = await self.rates_cache.get_float_rates()
                    if cached_rates:
                        self.logger.debug(
                            f"Returning {len(cached_rates)} float rates from cache",
                            extra={'event_type': 'cache_hit', 'cache_type': 'float'}
                        )
                        return self._convert_rates_to_xml_models(cached_rates)
                except Exception as cache_error:
                    self.logger.warning(
                        f"Cache error, falling back to API: {cache_error}",
                        extra={'event_type': 'cache_fallback', 'error': str(cache_error)}
                    )
            
            # Получаем из API
            if parse:
                rates_data = self.xml_api.get_rates_float_xml(parse=True)
                return self._convert_rates_to_xml_models(rates_data)
            else:
                # Return raw XML
                return self.xml_api.get_rates_float_xml(parse=False)
                
        except Exception as e:
            raise Exception(f"Failed to get float rates XML: {str(e)}")
    
    def _convert_rates_to_xml_models(self, rates_data: List[Dict[str, Any]]) -> List[XMLRate]:
        """Convert raw rates data to XMLRate models"""
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
    
    async def get_cached_rate_for_pair(
        self, 
        from_currency: str, 
        to_currency: str, 
        rate_type: str = "fixed"
    ) -> Optional[XMLRate]:
        """
        Get cached rate for specific currency pair
        
        Args:
            from_currency: Source currency code
            to_currency: Target currency code
            rate_type: "fixed" or "float"
            
        Returns:
            XMLRate if found in cache, None otherwise
        """
        if not settings.rates_cache_enabled:
            return None
            
        try:
            rate_data = await self.rates_cache.get_rate_for_pair(
                from_currency, to_currency, rate_type
            )
            if rate_data:
                return XMLRate(
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
            return None
        except Exception as e:
            self.logger.error(
                f"Failed to get cached rate for {from_currency}->{to_currency}: {e}",
                extra={'event_type': 'cache_error', 'error': str(e)}
            )
            return None
    
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
            reqConfirmations=data['to'].get('reqConfirmations', 0),
            maxConfirmations=data['to'].get('maxConfirmations', 0),
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
        
        # Handle back currency if exists and has valid code
        back_currency = None
        if 'back' in data and data['back'] and data['back'].get('code'):
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
                coin=data['back'].get('coin'),
                network=data['back'].get('network'),
                name=data['back'].get('name'),
                alias=data['back'].get('alias'),
                amount=data['back'].get('amount'),
                address=data['back'].get('address'),
                addressAlt=data['back'].get('addressAlt'),
                tag=data['back'].get('tag'),
                tagName=data['back'].get('tagName'),
                reqConfirmations=data['back'].get('reqConfirmations', 0),
                maxConfirmations=data['back'].get('maxConfirmations', 0),
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