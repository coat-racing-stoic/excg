"""
Redis кэширование для курсов обмена криптовалют
"""
import json
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime
import redis.asyncio as redis
from redis.asyncio.connection import ConnectionPool

from config import settings
from logging_config import get_logger

logger = get_logger('cache')


class RatesCache:
    """Сервис кэширования курсов обмена в Redis"""
    
    # Ключи для хранения в Redis
    FIXED_RATES_KEY = "rates:fixed"
    FLOAT_RATES_KEY = "rates:float"
    FIXED_RATES_TIMESTAMP_KEY = "rates:fixed:timestamp"
    FLOAT_RATES_TIMESTAMP_KEY = "rates:float:timestamp"
    CACHE_STATUS_KEY = "rates:cache:status"
    
    # TTL для кэша (в секундах) - немного больше интервала обновления
    CACHE_TTL = 60  # 1 минута
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or settings.redis_url
        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[redis.Redis] = None
        self._connected = False
        
    async def connect(self) -> bool:
        """Подключение к Redis"""
        try:
            self._pool = ConnectionPool.from_url(
                self.redis_url,
                max_connections=10,
                decode_responses=True
            )
            self._client = redis.Redis(connection_pool=self._pool)
            
            # Проверяем соединение
            await self._client.ping()
            self._connected = True
            logger.info("Successfully connected to Redis", extra={'event_type': 'redis_connected'})
            return True
            
        except Exception as e:
            logger.error(
                f"Failed to connect to Redis: {e}",
                extra={'event_type': 'redis_connection_error', 'error': str(e)}
            )
            self._connected = False
            return False
    
    async def disconnect(self):
        """Отключение от Redis"""
        if self._client:
            await self._client.close()
        if self._pool:
            await self._pool.disconnect()
        self._connected = False
        logger.info("Disconnected from Redis", extra={'event_type': 'redis_disconnected'})
    
    @property
    def is_connected(self) -> bool:
        """Проверка подключения к Redis"""
        return self._connected
    
    async def _ensure_connected(self):
        """Проверка и восстановление соединения"""
        if not self._connected:
            await self.connect()
        if not self._connected:
            raise ConnectionError("Redis is not available")
    
    async def set_fixed_rates(self, rates: List[Dict[str, Any]]) -> bool:
        """Сохранение фиксированных курсов в кэш"""
        try:
            await self._ensure_connected()
            
            timestamp = datetime.utcnow().isoformat() + 'Z'
            rates_json = json.dumps(rates, ensure_ascii=False)
            
            # Используем pipeline для атомарной операции
            async with self._client.pipeline() as pipe:
                await pipe.set(self.FIXED_RATES_KEY, rates_json, ex=self.CACHE_TTL)
                await pipe.set(self.FIXED_RATES_TIMESTAMP_KEY, timestamp, ex=self.CACHE_TTL)
                await pipe.execute()
            
            logger.info(
                f"Cached {len(rates)} fixed rates",
                extra={
                    'event_type': 'cache_update',
                    'cache_type': 'fixed',
                    'rates_count': len(rates),
                    'timestamp': timestamp
                }
            )
            return True
            
        except Exception as e:
            logger.error(
                f"Failed to cache fixed rates: {e}",
                extra={'event_type': 'cache_error', 'cache_type': 'fixed', 'error': str(e)}
            )
            return False
    
    async def set_float_rates(self, rates: List[Dict[str, Any]]) -> bool:
        """Сохранение плавающих курсов в кэш"""
        try:
            await self._ensure_connected()
            
            timestamp = datetime.utcnow().isoformat() + 'Z'
            rates_json = json.dumps(rates, ensure_ascii=False)
            
            async with self._client.pipeline() as pipe:
                await pipe.set(self.FLOAT_RATES_KEY, rates_json, ex=self.CACHE_TTL)
                await pipe.set(self.FLOAT_RATES_TIMESTAMP_KEY, timestamp, ex=self.CACHE_TTL)
                await pipe.execute()
            
            logger.info(
                f"Cached {len(rates)} float rates",
                extra={
                    'event_type': 'cache_update',
                    'cache_type': 'float',
                    'rates_count': len(rates),
                    'timestamp': timestamp
                }
            )
            return True
            
        except Exception as e:
            logger.error(
                f"Failed to cache float rates: {e}",
                extra={'event_type': 'cache_error', 'cache_type': 'float', 'error': str(e)}
            )
            return False
    
    async def get_fixed_rates(self) -> Optional[List[Dict[str, Any]]]:
        """Получение фиксированных курсов из кэша"""
        try:
            await self._ensure_connected()
            
            rates_json = await self._client.get(self.FIXED_RATES_KEY)
            if rates_json:
                rates = json.loads(rates_json)
                logger.debug(
                    f"Retrieved {len(rates)} fixed rates from cache",
                    extra={'event_type': 'cache_hit', 'cache_type': 'fixed'}
                )
                return rates
            
            logger.debug("Fixed rates cache miss", extra={'event_type': 'cache_miss', 'cache_type': 'fixed'})
            return None
            
        except Exception as e:
            logger.error(
                f"Failed to get fixed rates from cache: {e}",
                extra={'event_type': 'cache_error', 'cache_type': 'fixed', 'error': str(e)}
            )
            return None
    
    async def get_float_rates(self) -> Optional[List[Dict[str, Any]]]:
        """Получение плавающих курсов из кэша"""
        try:
            await self._ensure_connected()
            
            rates_json = await self._client.get(self.FLOAT_RATES_KEY)
            if rates_json:
                rates = json.loads(rates_json)
                logger.debug(
                    f"Retrieved {len(rates)} float rates from cache",
                    extra={'event_type': 'cache_hit', 'cache_type': 'float'}
                )
                return rates
            
            logger.debug("Float rates cache miss", extra={'event_type': 'cache_miss', 'cache_type': 'float'})
            return None
            
        except Exception as e:
            logger.error(
                f"Failed to get float rates from cache: {e}",
                extra={'event_type': 'cache_error', 'cache_type': 'float', 'error': str(e)}
            )
            return None
    
    async def get_cache_status(self) -> Dict[str, Any]:
        """Получение статуса кэша"""
        try:
            await self._ensure_connected()
            
            fixed_timestamp = await self._client.get(self.FIXED_RATES_TIMESTAMP_KEY)
            float_timestamp = await self._client.get(self.FLOAT_RATES_TIMESTAMP_KEY)
            
            fixed_ttl = await self._client.ttl(self.FIXED_RATES_KEY)
            float_ttl = await self._client.ttl(self.FLOAT_RATES_KEY)
            
            # Получаем количество записей
            fixed_rates = await self.get_fixed_rates()
            float_rates = await self.get_float_rates()
            
            return {
                "connected": self._connected,
                "fixed_rates": {
                    "count": len(fixed_rates) if fixed_rates else 0,
                    "last_update": fixed_timestamp,
                    "ttl_seconds": fixed_ttl if fixed_ttl > 0 else 0,
                    "cached": fixed_rates is not None
                },
                "float_rates": {
                    "count": len(float_rates) if float_rates else 0,
                    "last_update": float_timestamp,
                    "ttl_seconds": float_ttl if float_ttl > 0 else 0,
                    "cached": float_rates is not None
                }
            }
            
        except Exception as e:
            return {
                "connected": False,
                "error": str(e),
                "fixed_rates": {"cached": False},
                "float_rates": {"cached": False}
            }
    
    async def get_rate_for_pair(
        self, 
        from_currency: str, 
        to_currency: str, 
        rate_type: str = "fixed"
    ) -> Optional[Dict[str, Any]]:
        """Получение курса для конкретной пары валют"""
        try:
            if rate_type == "fixed":
                rates = await self.get_fixed_rates()
            else:
                rates = await self.get_float_rates()
            
            if not rates:
                return None
            
            # Ищем пару в кэше
            for rate in rates:
                if rate.get('from') == from_currency and rate.get('to') == to_currency:
                    return rate
            
            return None
            
        except Exception as e:
            logger.error(
                f"Failed to get rate for pair {from_currency}->{to_currency}: {e}",
                extra={'event_type': 'cache_error', 'error': str(e)}
            )
            return None
    
    async def invalidate_cache(self):
        """Инвалидация всего кэша курсов"""
        try:
            await self._ensure_connected()
            
            await self._client.delete(
                self.FIXED_RATES_KEY,
                self.FLOAT_RATES_KEY,
                self.FIXED_RATES_TIMESTAMP_KEY,
                self.FLOAT_RATES_TIMESTAMP_KEY
            )
            
            logger.info("Cache invalidated", extra={'event_type': 'cache_invalidated'})
            
        except Exception as e:
            logger.error(
                f"Failed to invalidate cache: {e}",
                extra={'event_type': 'cache_error', 'error': str(e)}
            )


# Глобальный экземпляр кэша
rates_cache = RatesCache()

