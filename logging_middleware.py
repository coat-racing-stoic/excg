"""
Middleware для логирования API запросов и ответов
"""
import time
import uuid
import json
import logging
from typing import Callable, Dict, Any, Optional
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from config import settings
from logging_config import get_logger, log_api_request, log_api_response, log_error

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware для логирования всех API запросов и ответов"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.api_logger = get_logger('api')
        self.error_logger = get_logger('error')
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Обрабатывает запрос и логирует его"""
        # Генерируем уникальный ID для запроса
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Получаем информацию о запросе
        method = request.method
        url = str(request.url)
        endpoint = request.url.path
        client_ip = self.get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        
        # Получаем API ключ если есть
        api_key = request.headers.get("x-api-key")
        
        # Читаем тело запроса для POST запросов
        request_data = None
        if method in ["POST", "PUT", "PATCH"] and settings.log_request_data:
            try:
                body = await request.body()
                if body:
                    request_data = json.loads(body.decode('utf-8'))
                    # Создаем новый Request с тем же телом
                    request = Request(request.scope, receive=self._make_receive(body))
            except (json.JSONDecodeError, UnicodeDecodeError):
                request_data = {"error": "Could not decode request body"}
        
        # Логируем запрос
        if settings.log_api_requests:
            log_api_request(
                self.api_logger,
                request_id=request_id,
                method=method,
                endpoint=endpoint,
                request_data=request_data,
                api_key=api_key
            )
            
            # Дополнительная информация в отдельном логе
            self.api_logger.info(
                f"Request details: {method} {endpoint}",
                extra={
                    'request_id': request_id,
                    'client_ip': client_ip,
                    'user_agent': user_agent,
                    'url': url,
                    'event_type': 'request_details'
                }
            )
        
        # Засекаем время начала обработки
        start_time = time.time()
        
        try:
            # Обрабатываем запрос
            response = await call_next(request)
            
            # Вычисляем время обработки
            process_time = time.time() - start_time
            
            # Получаем данные ответа если нужно
            response_data = None
            if settings.log_response_data and hasattr(response, 'body'):
                try:
                    if response.media_type == "application/json":
                        response_body = response.body
                        if response_body:
                            response_data = json.loads(response_body.decode('utf-8'))
                except (json.JSONDecodeError, UnicodeDecodeError, AttributeError):
                    response_data = {"error": "Could not decode response body"}
            
            # Логируем ответ
            if settings.log_api_responses:
                log_api_response(
                    self.api_logger,
                    request_id=request_id,
                    method=method,
                    endpoint=endpoint,
                    status_code=response.status_code,
                    response_time=process_time,
                    response_data=response_data,
                    api_key=api_key
                )
            
            # Добавляем заголовки для отладки
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{process_time:.3f}"
            
            return response
            
        except Exception as e:
            # Вычисляем время обработки
            process_time = time.time() - start_time
            
            # Логируем ошибку
            log_error(
                self.error_logger,
                error=e,
                request_id=request_id,
                context={
                    'method': method,
                    'endpoint': endpoint,
                    'client_ip': client_ip,
                    'api_key': api_key,
                    'process_time': process_time
                }
            )
            
            # Возвращаем ошибку в стандартном формате
            error_response = {
                "code": 500,
                "msg": "Internal server error",
                "data": {
                    "error": "An unexpected error occurred",
                    "request_id": request_id
                }
            }
            
            response = JSONResponse(
                content=error_response,
                status_code=500,
                headers={
                    "X-Request-ID": request_id,
                    "X-Process-Time": f"{process_time:.3f}"
                }
            )
            
            return response
    
    def get_client_ip(self, request: Request) -> str:
        """Получает IP адрес клиента"""
        # Проверяем заголовки прокси
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Возвращаем IP из соединения
        if hasattr(request.client, 'host'):
            return request.client.host
        
        return "unknown"
    
    def _make_receive(self, body: bytes):
        """Создает функцию receive для нового Request с тем же телом"""
        async def receive():
            return {"type": "http.request", "body": body}
        return receive

class RequestContextMiddleware(BaseHTTPMiddleware):
    """Middleware для добавления контекста запроса в логи"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Добавляет контекст запроса"""
        # Получаем или создаем request_id
        request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
        request.state.request_id = request_id
        
        # Добавляем контекст в логгер
        logger = get_logger('app')
        
        # Создаем адаптер логгера с контекстом
        class ContextLoggerAdapter(logging.LoggerAdapter):
            def process(self, msg, kwargs):
                kwargs.setdefault('extra', {}).update({
                    'request_id': request_id,
                    'endpoint': request.url.path,
                    'method': request.method
                })
                return msg, kwargs
        
        # Заменяем логгер в request.state
        request.state.logger = ContextLoggerAdapter(logger, {})
        
        response = await call_next(request)
        return response

def get_request_logger(request: Request) -> logging.Logger:
    """Получает логгер с контекстом запроса"""
    if hasattr(request.state, 'logger'):
        return request.state.logger
    return get_logger('app')

def get_request_id(request: Request) -> str:
    """Получает ID запроса"""
    return getattr(request.state, 'request_id', 'unknown')