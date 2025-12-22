"""
Фоновая задача для периодического обновления курсов обмена
"""
import asyncio
from typing import Optional
from datetime import datetime

from config import settings
from logging_config import get_logger
from redis_cache import rates_cache
from fixedfloatapi import FixedFloatApi

logger = get_logger('rates_updater')


class RatesUpdater:
    """Фоновый сервис обновления курсов обмена"""
    
    def __init__(self, update_interval: int = 20):
        """
        Args:
            update_interval: Интервал обновления в секундах (по умолчанию 20 сек)
        """
        self.update_interval = update_interval
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._api = FixedFloatApi(key=None, secret=None, logger=logger)
        self._consecutive_errors = 0
        self._max_consecutive_errors = 5
        
    async def start(self):
        """Запуск фоновой задачи обновления"""
        if self._running:
            logger.warning("Rates updater is already running")
            return
        
        # Подключаемся к Redis
        connected = await rates_cache.connect()
        if not connected:
            logger.error("Failed to connect to Redis, rates updater will not start")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._update_loop())
        logger.info(
            f"Rates updater started with {self.update_interval}s interval",
            extra={'event_type': 'updater_started', 'interval': self.update_interval}
        )
        
        # Выполняем первое обновление сразу
        await self._update_rates()
    
    async def stop(self):
        """Остановка фоновой задачи"""
        self._running = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        
        await rates_cache.disconnect()
        logger.info("Rates updater stopped", extra={'event_type': 'updater_stopped'})
    
    async def _update_loop(self):
        """Основной цикл обновления"""
        while self._running:
            try:
                await asyncio.sleep(self.update_interval)
                await self._update_rates()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self._consecutive_errors += 1
                logger.error(
                    f"Error in update loop: {e}",
                    extra={
                        'event_type': 'updater_error',
                        'error': str(e),
                        'consecutive_errors': self._consecutive_errors
                    }
                )
                
                # Если слишком много ошибок подряд, увеличиваем интервал
                if self._consecutive_errors >= self._max_consecutive_errors:
                    logger.warning(
                        f"Too many consecutive errors ({self._consecutive_errors}), "
                        f"increasing interval to {self.update_interval * 2}s"
                    )
                    await asyncio.sleep(self.update_interval * 2)
    
    async def _update_rates(self):
        """Обновление курсов из FixedFloat API"""
        start_time = datetime.utcnow()
        fixed_success = False
        float_success = False
        
        try:
            # Обновляем фиксированные курсы
            fixed_success = await self._update_fixed_rates()
            
            # Обновляем плавающие курсы
            float_success = await self._update_float_rates()
            
            # Сбрасываем счетчик ошибок при успехе
            if fixed_success and float_success:
                self._consecutive_errors = 0
            
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.info(
                f"Rates update completed in {duration:.2f}s",
                extra={
                    'event_type': 'rates_update_complete',
                    'duration': duration,
                    'fixed_success': fixed_success,
                    'float_success': float_success
                }
            )
            
        except Exception as e:
            self._consecutive_errors += 1
            logger.error(
                f"Failed to update rates: {e}",
                extra={'event_type': 'rates_update_error', 'error': str(e)}
            )
    
    async def _update_fixed_rates(self) -> bool:
        """Обновление фиксированных курсов"""
        try:
            # Получаем курсы из API (синхронный вызов в executor)
            loop = asyncio.get_event_loop()
            rates_data = await loop.run_in_executor(
                None, 
                lambda: self._api.get_rates_fixed_xml(parse=True)
            )
            
            if rates_data:
                await rates_cache.set_fixed_rates(rates_data)
                logger.debug(
                    f"Updated {len(rates_data)} fixed rates",
                    extra={'event_type': 'fixed_rates_updated', 'count': len(rates_data)}
                )
                return True
            
            return False
            
        except Exception as e:
            logger.error(
                f"Failed to update fixed rates: {e}",
                extra={'event_type': 'fixed_rates_error', 'error': str(e)}
            )
            return False
    
    async def _update_float_rates(self) -> bool:
        """Обновление плавающих курсов"""
        try:
            # Получаем курсы из API (синхронный вызов в executor)
            loop = asyncio.get_event_loop()
            rates_data = await loop.run_in_executor(
                None,
                lambda: self._api.get_rates_float_xml(parse=True)
            )
            
            if rates_data:
                await rates_cache.set_float_rates(rates_data)
                logger.debug(
                    f"Updated {len(rates_data)} float rates",
                    extra={'event_type': 'float_rates_updated', 'count': len(rates_data)}
                )
                return True
            
            return False
            
        except Exception as e:
            logger.error(
                f"Failed to update float rates: {e}",
                extra={'event_type': 'float_rates_error', 'error': str(e)}
            )
            return False
    
    async def force_update(self) -> dict:
        """Принудительное обновление курсов"""
        logger.info("Force update requested", extra={'event_type': 'force_update'})
        
        start_time = datetime.utcnow()
        fixed_success = await self._update_fixed_rates()
        float_success = await self._update_float_rates()
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        return {
            "success": fixed_success and float_success,
            "fixed_rates_updated": fixed_success,
            "float_rates_updated": float_success,
            "duration_seconds": duration,
            "timestamp": datetime.utcnow().isoformat() + 'Z'
        }
    
    @property
    def is_running(self) -> bool:
        """Проверка, запущен ли updater"""
        return self._running
    
    def get_status(self) -> dict:
        """Получение статуса updater"""
        return {
            "running": self._running,
            "update_interval": self.update_interval,
            "consecutive_errors": self._consecutive_errors,
            "max_consecutive_errors": self._max_consecutive_errors
        }


# Глобальный экземпляр updater
# Интервал обновления можно настроить через переменную окружения
UPDATE_INTERVAL = int(getattr(settings, 'rates_update_interval', 20))
rates_updater = RatesUpdater(update_interval=UPDATE_INTERVAL)

