# Crypto Exchange Backend API

Полнофункциональный back-end для обмена криптовалют, построенный на основе FixedFloat API с использованием FastAPI.

## Возможности

### Основные методы API
- ✅ **POST /api/v2/ccies** - Получение списка валют
- ✅ **POST /api/v2/price** - Получение курса обмена
- ✅ **POST /api/v2/create** - Создание ордера
- ✅ **POST /api/v2/order** - Получение информации об ордере
- ✅ **POST /api/v2/emergency** - Обработка аварийных ситуаций
- ✅ **POST /api/v2/setEmail** - Подписка на уведомления
- ✅ **POST /api/v2/qr** - Получение QR-кодов

### Бесплатные методы (без аутентификации)
- ✅ **GET /rates/fixed.xml** - XML экспорт курсов (фиксированный)
- ✅ **GET /rates/float.xml** - XML экспорт курсов (плавающий)
- ✅ **GET /api/rates/fixed** - JSON курсы (фиксированные)
- ✅ **GET /api/rates/float** - JSON курсы (плавающие)

### Дополнительные возможности
- 🔐 **Аутентификация** - X-API-KEY и X-API-SIGN заголовки
- ⚡ **Ограничение скорости** - 250 единиц в минуту, создание ордера 50 единиц
- 🤝 **Партнерская система** - Поддержка refcode и afftax параметров
- 📊 **Мониторинг** - Health check эндпоинт
- 📚 **Документация** - Автоматическая Swagger UI документация
- 🛡️ **Обработка ошибок** - Централизованная система обработки ошибок

## Быстрый старт

### 1. Установка зависимостей

```bash
cd crypto_exchange_backend
pip install -r requirements.txt
```

### 2. Настройка конфигурации

Скопируйте `.env.example` в `.env` и настройте параметры:

```bash
cp .env.example .env
```

Отредактируйте `.env`:
```env
# API Configuration
FIXEDFLOAT_API_KEY=your_api_key_here
FIXEDFLOAT_API_SECRET=your_api_secret_here

# Server Configuration
HOST=0.0.0.0
PORT=12000
DEBUG=True

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=250
RATE_LIMIT_CREATE_ORDER_WEIGHT=50
```

### 3. Запуск сервера

```bash
python main.py
```

Сервер будет доступен по адресу: http://localhost:12000

- **Swagger UI**: http://localhost:12000/docs
- **ReDoc**: http://localhost:12000/redoc
- **Health Check**: http://localhost:12000/health

## Примеры использования

### Получение списка валют

```bash
curl -X POST "http://localhost:12000/api/v2/ccies" \
  -H "X-API-KEY: your_api_key" \
  -H "X-API-SIGN: your_signature" \
  -H "Content-Type: application/json" \
  -d "{}"
```

### Получение курса обмена

```bash
curl -X POST "http://localhost:12000/api/v2/price" \
  -H "X-API-KEY: your_api_key" \
  -H "X-API-SIGN: your_signature" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "fixed",
    "fromCcy": "BTC",
    "toCcy": "ETH",
    "direction": "from",
    "amount": 0.1
  }'
```

### Создание ордера

```bash
curl -X POST "http://localhost:12000/api/v2/create" \
  -H "X-API-KEY: your_api_key" \
  -H "X-API-SIGN: your_signature" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "fixed",
    "fromCcy": "BTC",
    "toCcy": "ETH",
    "direction": "from",
    "amount": 0.1,
    "toAddress": "0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6"
  }'
```

### Получение статуса ордера

```bash
curl -X POST "http://localhost:12000/api/v2/order" \
  -H "X-API-KEY: your_api_key" \
  -H "X-API-SIGN: your_signature" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "ORDER_ID",
    "token": "ORDER_TOKEN"
  }'
```

### Получение курсов в XML (без аутентификации)

```bash
# Фиксированные курсы
curl "http://localhost:12000/rates/fixed.xml"

# Плавающие курсы
curl "http://localhost:12000/rates/float.xml"

# JSON формат
curl "http://localhost:12000/api/rates/fixed"
curl "http://localhost:12000/api/rates/float"
```

## Партнерская система

Поддерживается партнерская программа с автоматическим расчетом комиссий:

```bash
curl -X POST "http://localhost:12000/api/v2/price" \
  -H "X-API-KEY: your_api_key" \
  -H "X-API-SIGN: your_signature" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "fixed",
    "fromCcy": "BTC",
    "toCcy": "ETH",
    "direction": "from",
    "amount": 0.1,
    "refcode": "DEMO001",
    "afftax": 2.5
  }'
```

### Формулы расчета комиссий

1. **Если afftax < (FF - AFFB)**: `total = FF - AFFB + afftax`
2. **Если (FF - AFFB) ≤ afftax < FF**: `total = afftax × 2`
3. **Если afftax > FF**: `total = FF + afftax`

## Статусы ордеров

| Статус | Описание |
|--------|----------|
| NEW | Новый ордер |
| PENDING | Ожидание подтверждений |
| EXCHANGE | Обмен в процессе |
| WITHDRAW | Отправка средств |
| DONE | Завершен |
| EXPIRED | Истек |
| EMERGENCY | Аварийная ситуация |
| FAILED | Неудача |

## Лимиты и веса запросов

- **Общий лимит**: 250 весовых единиц в минуту
- **Создание ордера**: 50 единиц
- **Остальные запросы**: 1 единица
- **XML эндпоинты**: Неограниченно

## Обработка ошибок

API возвращает стандартизированные ошибки:

```json
{
  "code": 400,
  "msg": "Validation failed",
  "data": {
    "error": "Amount below minimum limit",
    "details": {
      "min_amount": 0.001,
      "provided_amount": 0.0005
    }
  }
}
```

### Коды ошибок

- **400** - Ошибка валидации
- **401** - Ошибка аутентификации
- **404** - Ресурс не найден
- **429** - Превышен лимит запросов
- **500** - Внутренняя ошибка сервера
- **502** - Ошибка FixedFloat API
- **503** - Сервис недоступен

## Аутентификация

Для аутентифицированных эндпоинтов требуются заголовки:

- **X-API-KEY**: Ваш API ключ
- **X-API-SIGN**: HMAC-SHA256 подпись тела запроса

### Создание подписи

```python
import hmac
import hashlib
import json

def create_signature(api_secret: str, data: dict) -> str:
    json_str = json.dumps(data, separators=(',', ':'), sort_keys=True)
    return hmac.new(
        api_secret.encode('utf-8'),
        json_str.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
```

## Развертывание

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 12000

CMD ["python", "main.py"]
```

### Docker Compose

```yaml
version: '3.8'
services:
  crypto-exchange-api:
    build: .
    ports:
      - "12000:12000"
    environment:
      - FIXEDFLOAT_API_KEY=${FIXEDFLOAT_API_KEY}
      - FIXEDFLOAT_API_SECRET=${FIXEDFLOAT_API_SECRET}
    volumes:
      - .env:/app/.env
```

## Мониторинг

### Health Check

```bash
curl "http://localhost:12000/health"
```

Ответ:
```json
{
  "status": "healthy",
  "timestamp": "2023-12-13T10:30:00.000Z",
  "version": "1.0.0"
}
```

### Метрики Rate Limiting

Заголовки ответа содержат информацию о лимитах:

```
X-RateLimit-Limit: 250
X-RateLimit-Remaining: 200
X-RateLimit-Reset: 1702467000
```

## Рекомендации

### Для массовых операций
- Используйте XML эндпоинты `/rates/fixed.xml` и `/rates/float.xml`
- Кешируйте данные локально (TTL 5-10 минут)

### Для создания ордеров
- Всегда сначала вызывайте `/api/v2/price`
- Проверяйте ошибки в ответе (`data.errors`)

### Для мониторинга
- Используйте `/api/v2/order` для проверки статуса
- Подписывайтесь на уведомления через `/api/v2/setEmail`

### Для обработки ошибок
- При статусе EMERGENCY используйте `/api/v2/emergency`
- Предоставляйте пользователю выбор действия

## Поддержка

Для получения поддержки:
1. Проверьте документацию API: http://localhost:12000/docs
2. Изучите примеры в этом README
3. Проверьте логи сервера для диагностики ошибок

## Лицензия

MIT License