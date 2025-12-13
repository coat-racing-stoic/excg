# Руководство по развертыванию Crypto Exchange Backend

## Обзор проекта

Полнофункциональный backend для обмена криптовалют, реализующий API спецификацию FixedFloat. Включает аутентификацию, ограничение скорости запросов, партнерскую систему и все необходимые endpoints.

## Архитектура

```
crypto_exchange_backend/
├── main.py                 # Основное FastAPI приложение
├── models.py              # Pydantic модели для запросов/ответов
├── auth.py                # Система аутентификации HMAC-SHA256
├── rate_limiter.py        # Ограничение скорости запросов
├── fixedfloat_service.py  # Интеграция с FixedFloat API
├── partner_system.py      # Партнерская программа
├── exceptions.py          # Обработка ошибок
├── config.py              # Конфигурация приложения
├── .env                   # Переменные окружения
├── requirements.txt       # Зависимости Python
├── Dockerfile            # Docker контейнер
├── docker-compose.yml    # Docker Compose конфигурация
├── nginx.conf            # Nginx конфигурация
└── examples/
    └── client_example.py  # Пример клиента
```

## Реализованные функции

### ✅ API Endpoints
1. **POST /api/v2/ccies** - Получение списка валют
2. **POST /api/v2/price** - Получение курса обмена
3. **POST /api/v2/create** - Создание ордера
4. **POST /api/v2/order** - Информация об ордере
5. **POST /api/v2/emergency** - Обработка аварийных ситуаций
6. **POST /api/v2/setEmail** - Подписка на уведомления
7. **POST /api/v2/qr** - Получение QR-кодов
8. **GET /api/rates/fixed** - XML экспорт фиксированных курсов
9. **GET /api/rates/float** - XML экспорт плавающих курсов

### ✅ Безопасность
- HMAC-SHA256 аутентификация с X-API-KEY и X-API-SIGN заголовками
- Валидация подписи для всех защищенных endpoints
- CORS поддержка для веб-приложений

### ✅ Ограничение скорости
- 250 весовых единиц в минуту
- Создание ордера: 50 единиц
- Остальные запросы: 1 единица
- Redis для хранения состояния

### ✅ Партнерская система
- Поддержка refcode и afftax параметров
- Расчет комиссий по формулам FixedFloat
- Интеграция во все соответствующие endpoints

### ✅ Обработка ошибок
- Централизованная обработка исключений
- Правильные HTTP статус коды
- Детальные сообщения об ошибках

## Быстрый старт

### 1. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 2. Настройка переменных окружения
```bash
cp .env.example .env
# Отредактируйте .env файл с вашими API ключами
```

### 3. Запуск приложения
```bash
python main.py
```

Приложение будет доступно по адресу: http://localhost:12000

### 4. Документация API
- Swagger UI: http://localhost:12000/docs
- ReDoc: http://localhost:12000/redoc

## Docker развертывание

### Простой запуск
```bash
docker-compose up -d
```

### Ручная сборка
```bash
docker build -t crypto-exchange-backend .
docker run -p 12000:12000 crypto-exchange-backend
```

## Тестирование

### Запуск тестов
```bash
python test_api.py
```

### Пример использования клиента
```bash
python examples/client_example.py
```

## Конфигурация

### Переменные окружения (.env)
```env
# FixedFloat API
FIXEDFLOAT_API_KEY=your_api_key_here
FIXEDFLOAT_API_SECRET=your_api_secret_here

# Сервер
HOST=0.0.0.0
PORT=12000
DEBUG=True

# Redis
REDIS_URL=redis://localhost:6379/0

# Безопасность
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256

# Ограничения
RATE_LIMIT_REQUESTS_PER_MINUTE=250
RATE_LIMIT_CREATE_ORDER_WEIGHT=50
RATE_LIMIT_DEFAULT_WEIGHT=1
```

## Мониторинг

### Health Check
```bash
curl http://localhost:12000/health
```

### Метрики
- Логи запросов в stdout
- Rate limiting headers в ответах
- Детальная информация об ошибках

## Производственное развертывание

### Рекомендации
1. Используйте HTTPS (настройте reverse proxy)
2. Настройте мониторинг и логирование
3. Используйте внешний Redis кластер
4. Настройте автоматическое масштабирование
5. Регулярно обновляйте зависимости

### Nginx конфигурация
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:12000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Поддержка

### Логи
Все логи выводятся в stdout и могут быть перенаправлены в систему логирования.

### Отладка
Установите `DEBUG=True` в .env для детального логирования.

### Известные проблемы
- API ключи FixedFloat должны быть активными для работы с внешним API
- Redis должен быть доступен для rate limiting

## Лицензия

MIT License - см. LICENSE файл для деталей.