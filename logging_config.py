"""
Конфигурация системы логирования для Crypto Exchange Backend
"""
import logging
import logging.handlers
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

class JSONFormatter(logging.Formatter):
    """Форматтер для структурированного JSON логирования"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Форматирует запись лога в JSON"""
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Добавляем дополнительные поля если они есть
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'api_key'):
            log_entry['api_key'] = record.api_key[:8] + '...' if record.api_key else None
        if hasattr(record, 'endpoint'):
            log_entry['endpoint'] = record.endpoint
        if hasattr(record, 'method'):
            log_entry['method'] = record.method
        if hasattr(record, 'status_code'):
            log_entry['status_code'] = record.status_code
        if hasattr(record, 'response_time'):
            log_entry['response_time'] = record.response_time
        if hasattr(record, 'request_data'):
            log_entry['request_data'] = record.request_data
        if hasattr(record, 'response_data'):
            log_entry['response_data'] = record.response_data
        if hasattr(record, 'error_type'):
            log_entry['error_type'] = record.error_type
        if hasattr(record, 'error_details'):
            log_entry['error_details'] = record.error_details
        
        # Добавляем информацию об исключении если есть
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__ if record.exc_info[0] else None,
                'message': str(record.exc_info[1]) if record.exc_info[1] else None,
                'traceback': self.formatException(record.exc_info)
            }
        
        return json.dumps(log_entry, ensure_ascii=False, default=str)

class LoggingConfig:
    """Конфигурация системы логирования"""
    
    def __init__(self, log_dir: str = "logs", debug: bool = False):
        self.log_dir = Path(log_dir)
        self.debug = debug
        self.log_dir.mkdir(exist_ok=True)
        
    def setup_logging(self):
        """Настраивает систему логирования"""
        # Создаем основной логгер
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG if self.debug else logging.INFO)
        
        # Очищаем существующие обработчики
        root_logger.handlers.clear()
        
        # Консольный обработчик
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
        
        # Файловый обработчик для общих логов
        general_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "app.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        general_handler.setLevel(logging.INFO)
        general_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(general_handler)
        
        # Файловый обработчик для ошибок
        error_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "errors.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=10,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(error_handler)
        
        # Файловый обработчик для API запросов
        api_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "api.log",
            maxBytes=50*1024*1024,  # 50MB
            backupCount=10,
            encoding='utf-8'
        )
        api_handler.setLevel(logging.INFO)
        api_handler.setFormatter(JSONFormatter())
        
        # Создаем специальный логгер для API
        api_logger = logging.getLogger('api')
        api_logger.setLevel(logging.INFO)
        api_logger.addHandler(api_handler)
        api_logger.propagate = False  # Не передаем в root logger
        
        # Файловый обработчик для FixedFloat API
        fixedfloat_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "fixedfloat.log",
            maxBytes=20*1024*1024,  # 20MB
            backupCount=5,
            encoding='utf-8'
        )
        fixedfloat_handler.setLevel(logging.INFO)
        fixedfloat_handler.setFormatter(JSONFormatter())
        
        # Создаем специальный логгер для FixedFloat
        fixedfloat_logger = logging.getLogger('fixedfloat')
        fixedfloat_logger.setLevel(logging.INFO)
        fixedfloat_logger.addHandler(fixedfloat_handler)
        fixedfloat_logger.propagate = False
        
        # Настраиваем логгеры для внешних библиотек
        logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
        logging.getLogger('httpx').setLevel(logging.WARNING)
        logging.getLogger('httpcore').setLevel(logging.WARNING)
        
        logging.info("Logging system initialized")

def get_logger(name: str) -> logging.Logger:
    """Получает логгер с указанным именем"""
    return logging.getLogger(name)

def log_api_request(
    logger: logging.Logger,
    request_id: str,
    method: str,
    endpoint: str,
    request_data: Optional[Dict[str, Any]] = None,
    api_key: Optional[str] = None,
    user_id: Optional[str] = None
):
    """Логирует API запрос"""
    logger.info(
        f"API Request: {method} {endpoint}",
        extra={
            'request_id': request_id,
            'method': method,
            'endpoint': endpoint,
            'request_data': request_data,
            'api_key': api_key,
            'user_id': user_id,
            'event_type': 'api_request'
        }
    )

def log_api_response(
    logger: logging.Logger,
    request_id: str,
    method: str,
    endpoint: str,
    status_code: int,
    response_time: float,
    response_data: Optional[Dict[str, Any]] = None,
    api_key: Optional[str] = None,
    user_id: Optional[str] = None
):
    """Логирует API ответ"""
    logger.info(
        f"API Response: {method} {endpoint} - {status_code} ({response_time:.3f}s)",
        extra={
            'request_id': request_id,
            'method': method,
            'endpoint': endpoint,
            'status_code': status_code,
            'response_time': response_time,
            'response_data': response_data,
            'api_key': api_key,
            'user_id': user_id,
            'event_type': 'api_response'
        }
    )

def log_fixedfloat_request(
    logger: logging.Logger,
    request_id: str,
    method: str,
    url: str,
    request_data: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None
):
    """Логирует запрос к FixedFloat API"""
    # Скрываем чувствительные данные в заголовках
    safe_headers = {}
    if headers:
        for key, value in headers.items():
            if key.lower() in ['x-api-key', 'x-api-sign']:
                safe_headers[key] = value[:8] + '...' if value else None
            else:
                safe_headers[key] = value
    
    logger.info(
        f"FixedFloat Request: {method} {url}",
        extra={
            'request_id': request_id,
            'method': method,
            'url': url,
            'request_data': request_data,
            'headers': safe_headers,
            'event_type': 'fixedfloat_request'
        }
    )

def log_fixedfloat_response(
    logger: logging.Logger,
    request_id: str,
    method: str,
    url: str,
    status_code: int,
    response_time: float,
    response_data: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None
):
    """Логирует ответ от FixedFloat API"""
    if error:
        logger.error(
            f"FixedFloat Error: {method} {url} - {status_code} ({response_time:.3f}s): {error}",
            extra={
                'request_id': request_id,
                'method': method,
                'url': url,
                'status_code': status_code,
                'response_time': response_time,
                'response_data': response_data,
                'error_type': 'fixedfloat_api_error',
                'error_details': error,
                'event_type': 'fixedfloat_error'
            }
        )
    else:
        logger.info(
            f"FixedFloat Response: {method} {url} - {status_code} ({response_time:.3f}s)",
            extra={
                'request_id': request_id,
                'method': method,
                'url': url,
                'status_code': status_code,
                'response_time': response_time,
                'response_data': response_data,
                'event_type': 'fixedfloat_response'
            }
        )

def log_error(
    logger: logging.Logger,
    error: Exception,
    request_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
):
    """Логирует ошибку с дополнительным контекстом"""
    logger.error(
        f"Error: {type(error).__name__}: {str(error)}",
        extra={
            'request_id': request_id,
            'error_type': type(error).__name__,
            'error_details': str(error),
            'context': context,
            'event_type': 'error'
        },
        exc_info=True
    )