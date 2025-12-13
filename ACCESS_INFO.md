# 🌐 Доступ к Crypto Exchange Backend

## 🚀 Приложение запущено и готово к использованию!

### 📍 Основные URL
- **Основной API**: http://localhost:12000
- **Swagger UI**: http://localhost:12000/docs
- **ReDoc**: http://localhost:12000/redoc
- **Health Check**: http://localhost:12000/health

### 🌍 Внешний доступ (через браузер)
Приложение также доступно по внешним URL:
- **Основной API**: https://work-1-yiasrhcqtcuxuryd.prod-runtime.all-hands.dev
- **Swagger UI**: https://work-1-yiasrhcqtcuxuryd.prod-runtime.all-hands.dev/docs
- **ReDoc**: https://work-1-yiasrhcqtcuxuryd.prod-runtime.all-hands.dev/redoc
- **Health Check**: https://work-1-yiasrhcqtcuxuryd.prod-runtime.all-hands.dev/health

## 🧪 Быстрая проверка

### 1. Health Check
```bash
curl https://work-1-yiasrhcqtcuxuryd.prod-runtime.all-hands.dev/health
```

### 2. Получение курсов (без аутентификации)
```bash
curl https://work-1-yiasrhcqtcuxuryd.prod-runtime.all-hands.dev/api/rates/fixed
```

### 3. Swagger UI
Откройте в браузере: https://work-1-yiasrhcqtcuxuryd.prod-runtime.all-hands.dev/docs

## 🔐 Аутентификация

Для тестирования защищенных endpoints используйте:
- **API Key**: `WTyKYfiWHx4ayHfhDY5mEVXkI6eFYv418whIrPiQ`
- **API Secret**: `CUuJ5jIspDOYmEsu5gr11l4RuAjacMGgDJ7TzmUq`

### Пример запроса с аутентификацией:
```bash
# Создание подписи для данных
DATA='{"type": "fixed", "fromCcy": "BTC", "toCcy": "ETH", "direction": "from", "amount": 0.1}'
SIGNATURE=$(echo -n "$DATA" | openssl dgst -sha256 -hmac "CUuJ5jIspDOYmEsu5gr11l4RuAjacMGgDJ7TzmUq" | cut -d' ' -f2)

# Отправка запроса
curl -X POST "https://work-1-yiasrhcqtcuxuryd.prod-runtime.all-hands.dev/api/v2/price" \
  -H "Content-Type: application/json; charset=UTF-8" \
  -H "X-API-KEY: WTyKYfiWHx4ayHfhDY5mEVXkI6eFYv418whIrPiQ" \
  -H "X-API-SIGN: $SIGNATURE" \
  -d "$DATA"
```

## 📊 Статус системы

### ✅ Работающие компоненты:
- FastAPI сервер на порту 12000
- Все 9 API endpoints
- Система аутентификации HMAC-SHA256
- Rate limiting с Redis
- Партнерская система
- Обработка ошибок
- Swagger UI документация

### ✅ Примечания:
- API ключи FixedFloat активны и работают
- Все endpoints полностью функциональны
- Redis работает локально для rate limiting
- Партнерские параметры не поддерживаются для данного типа API ключа

## 🛠️ Для разработчиков

### Локальная разработка:
```bash
cd /workspace/project/crypto_exchange_backend
python main.py
```

### Тестирование:
```bash
python test_api.py
```

### Пример клиента:
```bash
python examples/client_example.py
```

## 📚 Документация

- **README.md** - Основная документация
- **DEPLOYMENT_GUIDE.md** - Руководство по развертыванию
- **PROJECT_SUMMARY.md** - Итоговый отчет проекта
- **examples/client_example.py** - Пример использования

## 🎉 Готово к использованию!

Crypto Exchange Backend полностью реализован и готов к использованию. Все endpoints работают согласно спецификации FixedFloat API.