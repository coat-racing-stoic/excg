"""
Валидация доступных валют с кэшированием (TTL 1 час)
"""
import json
import asyncio
from typing import Optional, List, Dict, Set, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import redis.asyncio as redis

from config import settings
from logging_config import get_logger

logger = get_logger('currency_validator')


@dataclass
class CurrencyInfo:
    """Информация о валюте"""
    code: str
    coin: str
    network: str
    name: str
    recv: bool  # Можно получать
    send: bool  # Можно отправлять
    tag: Optional[str] = None


class CurrencyValidator:
    """
    Сервис валидации валют с кэшированием в Redis.
    TTL кэша: 1 час (3600 секунд)
    """
    
    # Ключи Redis
    CURRENCIES_KEY = "currencies:list"
    CURRENCIES_TIMESTAMP_KEY = "currencies:timestamp"
    SENDABLE_CURRENCIES_KEY = "currencies:sendable"
    RECEIVABLE_CURRENCIES_KEY = "currencies:receivable"
    
    # TTL кэша - 1 час
    CACHE_TTL = 3600
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or settings.redis_url
        self._client: Optional[redis.Redis] = None
        self._connected = False
        
        # In-memory fallback кэш (если Redis недоступен)
        self._memory_cache: Dict[str, CurrencyInfo] = {}
        self._memory_cache_timestamp: Optional[datetime] = None
        self._sendable_codes: Set[str] = set()
        self._receivable_codes: Set[str] = set()
    
    async def connect(self) -> bool:
        """Подключение к Redis"""
        try:
            self._client = redis.from_url(
                self.redis_url,
                decode_responses=True
            )
            await self._client.ping()
            self._connected = True
            logger.info("Currency validator connected to Redis", extra={'event_type': 'redis_connected'})
            return True
        except Exception as e:
            logger.warning(
                f"Currency validator failed to connect to Redis, using memory cache: {e}",
                extra={'event_type': 'redis_connection_error', 'error': str(e)}
            )
            self._connected = False
            return False
    
    async def disconnect(self):
        """Отключение от Redis"""
        if self._client:
            await self._client.close()
        self._connected = False
    
    async def _ensure_connected(self):
        """Проверка соединения"""
        if not self._connected:
            await self.connect()
    
    async def update_currencies(self, currencies: List[Dict]) -> bool:
        """
        Обновление списка валют в кэше.
        Вызывается после получения списка валют от FixedFloat API.
        """
        try:
            timestamp = datetime.utcnow().isoformat() + 'Z'
            
            # Подготовка данных
            sendable_codes = []
            receivable_codes = []
            currencies_data = {}
            
            for curr in currencies:
                code = curr.get('code', '')
                if not code:
                    continue
                    
                currencies_data[code] = {
                    'code': code,
                    'coin': curr.get('coin', ''),
                    'network': curr.get('network', ''),
                    'name': curr.get('name', ''),
                    'recv': curr.get('recv', False),
                    'send': curr.get('send', False),
                    'tag': curr.get('tag')
                }
                
                if curr.get('send', False):
                    sendable_codes.append(code)
                if curr.get('recv', False):
                    receivable_codes.append(code)
            
            # Обновляем in-memory кэш
            self._memory_cache = {
                code: CurrencyInfo(**data) for code, data in currencies_data.items()
            }
            self._memory_cache_timestamp = datetime.utcnow()
            self._sendable_codes = set(sendable_codes)
            self._receivable_codes = set(receivable_codes)
            
            # Пытаемся сохранить в Redis
            await self._ensure_connected()
            if self._connected:
                try:
                    async with self._client.pipeline() as pipe:
                        await pipe.set(
                            self.CURRENCIES_KEY, 
                            json.dumps(currencies_data, ensure_ascii=False),
                            ex=self.CACHE_TTL
                        )
                        await pipe.set(
                            self.CURRENCIES_TIMESTAMP_KEY,
                            timestamp,
                            ex=self.CACHE_TTL
                        )
                        await pipe.set(
                            self.SENDABLE_CURRENCIES_KEY,
                            json.dumps(sendable_codes),
                            ex=self.CACHE_TTL
                        )
                        await pipe.set(
                            self.RECEIVABLE_CURRENCIES_KEY,
                            json.dumps(receivable_codes),
                            ex=self.CACHE_TTL
                        )
                        await pipe.execute()
                    
                    logger.info(
                        f"Cached {len(currencies_data)} currencies (TTL: {self.CACHE_TTL}s)",
                        extra={
                            'event_type': 'currencies_cached',
                            'total_count': len(currencies_data),
                            'sendable_count': len(sendable_codes),
                            'receivable_count': len(receivable_codes),
                            'ttl': self.CACHE_TTL
                        }
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to cache currencies in Redis: {e}",
                        extra={'event_type': 'cache_error', 'error': str(e)}
                    )
            
            return True
            
        except Exception as e:
            logger.error(
                f"Failed to update currencies: {e}",
                extra={'event_type': 'currencies_update_error', 'error': str(e)}
            )
            return False
    
    async def _load_from_redis(self) -> bool:
        """Загрузка данных из Redis в memory кэш"""
        try:
            await self._ensure_connected()
            if not self._connected:
                return False
            
            currencies_json = await self._client.get(self.CURRENCIES_KEY)
            if not currencies_json:
                return False
            
            currencies_data = json.loads(currencies_json)
            sendable_json = await self._client.get(self.SENDABLE_CURRENCIES_KEY)
            receivable_json = await self._client.get(self.RECEIVABLE_CURRENCIES_KEY)
            
            self._memory_cache = {
                code: CurrencyInfo(**data) for code, data in currencies_data.items()
            }
            self._sendable_codes = set(json.loads(sendable_json)) if sendable_json else set()
            self._receivable_codes = set(json.loads(receivable_json)) if receivable_json else set()
            self._memory_cache_timestamp = datetime.utcnow()
            
            logger.debug(
                f"Loaded {len(self._memory_cache)} currencies from Redis cache",
                extra={'event_type': 'cache_loaded'}
            )
            return True
            
        except Exception as e:
            logger.warning(
                f"Failed to load currencies from Redis: {e}",
                extra={'event_type': 'cache_load_error', 'error': str(e)}
            )
            return False
    
    def _is_memory_cache_valid(self) -> bool:
        """Проверка валидности in-memory кэша"""
        if not self._memory_cache or not self._memory_cache_timestamp:
            return False
        
        age = datetime.utcnow() - self._memory_cache_timestamp
        return age.total_seconds() < self.CACHE_TTL
    
    async def _ensure_cache_loaded(self) -> bool:
        """Убедиться что кэш загружен"""
        if self._is_memory_cache_valid():
            return True
        
        # Пытаемся загрузить из Redis
        if await self._load_from_redis():
            return True
        
        # Кэш пуст - нужно обновить
        return False
    
    async def is_valid_currency(self, code: str) -> bool:
        """Проверка существования валюты"""
        if not await self._ensure_cache_loaded():
            logger.warning(
                "Currency cache is empty, cannot validate",
                extra={'event_type': 'validation_skipped', 'reason': 'empty_cache'}
            )
            return True  # Пропускаем валидацию если кэш пуст
        
        return code in self._memory_cache
    
    async def is_sendable(self, code: str) -> bool:
        """Проверка что валюту можно отправить (fromCcy)"""
        if not await self._ensure_cache_loaded():
            return True  # Пропускаем валидацию если кэш пуст
        
        return code in self._sendable_codes
    
    async def is_receivable(self, code: str) -> bool:
        """Проверка что валюту можно получить (toCcy)"""
        if not await self._ensure_cache_loaded():
            return True  # Пропускаем валидацию если кэш пуст
        
        return code in self._receivable_codes
    
    async def validate_pair(self, from_ccy: str, to_ccy: str) -> Tuple[bool, Optional[str]]:
        """
        Валидация пары валют для обмена.
        
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if not await self._ensure_cache_loaded():
            logger.warning(
                "Currency cache is empty, skipping pair validation",
                extra={
                    'event_type': 'validation_skipped',
                    'from_ccy': from_ccy,
                    'to_ccy': to_ccy
                }
            )
            return True, None
        
        # Проверяем fromCcy
        if from_ccy not in self._memory_cache:
            return False, f"Unknown currency: {from_ccy}"
        
        if not self._memory_cache[from_ccy].send:
            return False, f"Currency {from_ccy} is not available for sending"
        
        # Проверяем toCcy
        if to_ccy not in self._memory_cache:
            return False, f"Unknown currency: {to_ccy}"
        
        if not self._memory_cache[to_ccy].recv:
            return False, f"Currency {to_ccy} is not available for receiving"
        
        # Проверяем что это разные валюты
        if from_ccy == to_ccy:
            return False, "Source and destination currencies must be different"
        
        logger.debug(
            f"Pair validation passed: {from_ccy} -> {to_ccy}",
            extra={
                'event_type': 'pair_validated',
                'from_ccy': from_ccy,
                'to_ccy': to_ccy
            }
        )
        
        return True, None
    
    async def get_currency_info(self, code: str) -> Optional[CurrencyInfo]:
        """Получение информации о валюте"""
        if not await self._ensure_cache_loaded():
            return None
        
        return self._memory_cache.get(code)
    
    async def get_all_currencies(self) -> List[CurrencyInfo]:
        """Получение списка всех валют"""
        if not await self._ensure_cache_loaded():
            return []
        
        return list(self._memory_cache.values())
    
    async def get_sendable_currencies(self) -> List[str]:
        """Получение списка валют доступных для отправки"""
        if not await self._ensure_cache_loaded():
            return []
        
        return list(self._sendable_codes)
    
    async def get_receivable_currencies(self) -> List[str]:
        """Получение списка валют доступных для получения"""
        if not await self._ensure_cache_loaded():
            return []
        
        return list(self._receivable_codes)
    
    async def get_cache_status(self) -> Dict:
        """Получение статуса кэша валют"""
        status = {
            "memory_cache": {
                "count": len(self._memory_cache),
                "sendable_count": len(self._sendable_codes),
                "receivable_count": len(self._receivable_codes),
                "timestamp": self._memory_cache_timestamp.isoformat() if self._memory_cache_timestamp else None,
                "valid": self._is_memory_cache_valid()
            },
            "ttl_seconds": self.CACHE_TTL,
            "redis_connected": self._connected
        }
        
        # Проверяем Redis
        if self._connected:
            try:
                ttl = await self._client.ttl(self.CURRENCIES_KEY)
                status["redis_cache"] = {
                    "ttl_remaining": ttl if ttl > 0 else 0,
                    "exists": ttl > 0
                }
            except Exception:
                status["redis_cache"] = {"exists": False}
        
        return status


# Глобальный экземпляр валидатора
currency_validator = CurrencyValidator()
