# 🔐 Руководство по аутентификации Crypto Exchange Backend

## Ошибка 401: Missing X-API-KEY or X-API-SIGN headers

Эта ошибка возникает, когда вы пытаетесь обратиться к защищенному endpoint без необходимых заголовков аутентификации.

## 📋 Требования для аутентификации

Для всех защищенных endpoints (кроме `/health`, `/api/rates/fixed`, `/api/rates/float`) требуются **обязательные заголовки**:

- **Content-Type**: `application/json; charset=UTF-8` (обязательно с charset!)
- **X-API-KEY**: Ваш API ключ FixedFloat  
- **X-API-SIGN**: HMAC-SHA256 подпись тела запроса

### ⚠️ ВАЖНО: Спецификация FixedFloat API

Согласно официальной спецификации FixedFloat API:

1. **Content-Type** должен быть `application/json; charset=UTF-8`
2. **X-API-KEY** должен содержать ваш API Key
3. **X-API-SIGN** должен содержать подпись, созданную с помощью HMAC SHA256, где:
   - Ключ: ваш API Secret
   - Значение: строка JSON данных запроса

## 🔑 Активные API ключи

```
API Key: WTyKYfiWHx4ayHfhDY5mEVXkI6eFYv418whIrPiQ
API Secret: CUuJ5jIspDOYmEsu5gr11l4RuAjacMGgDJ7TzmUq
```

## 🛠️ Как создать правильный запрос

### 1. Python пример

```python
import requests
import json
import hmac
import hashlib

# Конфигурация
API_KEY = "WTyKYfiWHx4ayHfhDY5mEVXkI6eFYv418whIrPiQ"
API_SECRET = "CUuJ5jIspDOYmEsu5gr11l4RuAjacMGgDJ7TzmUq"
BASE_URL = "https://work-1-yiasrhcqtcuxuryd.prod-runtime.all-hands.dev"

# Данные запроса
data = {
    "type": "fixed",
    "fromCcy": "BTC",
    "toCcy": "ETH",
    "direction": "from",
    "amount": 0.1
}

# Создание подписи (ВАЖНО: без сортировки ключей!)
json_str = json.dumps(data, separators=(', ', ': '))
signature = hmac.new(
    API_SECRET.encode('utf-8'),
    json_str.encode('utf-8'),
    hashlib.sha256
).hexdigest()

# Заголовки
headers = {
    'Content-Type': 'application/json; charset=UTF-8',
    'X-API-KEY': API_KEY,
    'X-API-SIGN': signature
}

# Отправка запроса
response = requests.post(f"{BASE_URL}/api/v2/price", headers=headers, json=data)
print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")
```

### 2. cURL пример

```bash
# Данные запроса
DATA='{"type": "fixed", "fromCcy": "BTC", "toCcy": "ETH", "direction": "from", "amount": 0.1}'

# Создание подписи
SIGNATURE=$(echo -n "$DATA" | openssl dgst -sha256 -hmac "CUuJ5jIspDOYmEsu5gr11l4RuAjacMGgDJ7TzmUq" | cut -d' ' -f2)

# Отправка запроса
curl -X POST "https://work-1-yiasrhcqtcuxuryd.prod-runtime.all-hands.dev/api/v2/price" \
  -H "Content-Type: application/json; charset=UTF-8" \
  -H "X-API-KEY: WTyKYfiWHx4ayHfhDY5mEVXkI6eFYv418whIrPiQ" \
  -H "X-API-SIGN: $SIGNATURE" \
  -d "$DATA"
```

### 3. JavaScript пример

```javascript
const crypto = require('crypto');

const API_KEY = 'WTyKYfiWHx4ayHfhDY5mEVXkI6eFYv418whIrPiQ';
const API_SECRET = 'CUuJ5jIspDOYmEsu5gr11l4RuAjacMGgDJ7TzmUq';
const BASE_URL = 'https://work-1-yiasrhcqtcuxuryd.prod-runtime.all-hands.dev';

// Данные запроса
const data = {
    type: 'fixed',
    fromCcy: 'BTC',
    toCcy: 'ETH',
    direction: 'from',
    amount: 0.1
};

// Создание подписи
const jsonStr = JSON.stringify(data);
const signature = crypto
    .createHmac('sha256', API_SECRET)
    .update(jsonStr)
    .digest('hex');

// Отправка запроса
fetch(`${BASE_URL}/api/v2/price`, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json; charset=UTF-8',
        'X-API-KEY': API_KEY,
        'X-API-SIGN': signature
    },
    body: jsonStr
})
.then(response => response.json())
.then(data => console.log(data));
```

## 🚫 Endpoints БЕЗ аутентификации

Эти endpoints можно вызывать без заголовков:

```bash
# Health check
curl "https://work-1-yiasrhcqtcuxuryd.prod-runtime.all-hands.dev/health"

# Фиксированные курсы (JSON)
curl "https://work-1-yiasrhcqtcuxuryd.prod-runtime.all-hands.dev/api/rates/fixed"

# Плавающие курсы (JSON)
curl "https://work-1-yiasrhcqtcuxuryd.prod-runtime.all-hands.dev/api/rates/float"

# XML курсы
curl "https://work-1-yiasrhcqtcuxuryd.prod-runtime.all-hands.dev/rates/fixed.xml"
curl "https://work-1-yiasrhcqtcuxuryd.prod-runtime.all-hands.dev/rates/float.xml"
```

## 🔒 Endpoints С аутентификацией

Эти endpoints требуют X-API-KEY и X-API-SIGN заголовки:

- `POST /api/v2/ccies` - Список валют
- `POST /api/v2/price` - Курс обмена
- `POST /api/v2/create` - Создание ордера
- `POST /api/v2/order` - Информация об ордере
- `POST /api/v2/emergency` - Аварийные ситуации
- `POST /api/v2/setEmail` - Подписка на уведомления
- `POST /api/v2/qr` - QR-коды

## ⚠️ Важные моменты

### 1. Порядок ключей в JSON
**КРИТИЧНО**: При создании подписи НЕ сортируйте ключи в JSON!

```python
# ✅ ПРАВИЛЬНО
json_str = json.dumps(data, separators=(', ', ': '))

# ❌ НЕПРАВИЛЬНО
json_str = json.dumps(data, separators=(', ', ': '), sort_keys=True)
```

### 2. Формат JSON
Используйте пробелы после запятых и двоеточий:
```json
{"type": "fixed", "fromCcy": "BTC", "toCcy": "ETH", "direction": "from", "amount": 0.1}
```

### 3. Кодировка
Всегда используйте UTF-8 кодировку для создания подписи.

## 🧪 Тестирование в Swagger UI

1. Откройте: https://work-1-yiasrhcqtcuxuryd.prod-runtime.all-hands.dev/docs
2. Нажмите "Authorize" в правом верхнем углу
3. Введите API ключ: `WTyKYfiWHx4ayHfhDY5mEVXkI6eFYv418whIrPiQ`
4. Swagger UI автоматически создаст правильную подпись

## 📞 Готовые примеры

### Получение списка валют
```bash
curl -X POST "https://work-1-yiasrhcqtcuxuryd.prod-runtime.all-hands.dev/api/v2/ccies" \
  -H "Content-Type: application/json; charset=UTF-8" \
  -H "X-API-KEY: WTyKYfiWHx4ayHfhDY5mEVXkI6eFYv418whIrPiQ" \
  -H "X-API-SIGN: $(echo -n '{}' | openssl dgst -sha256 -hmac 'CUuJ5jIspDOYmEsu5gr11l4RuAjacMGgDJ7TzmUq' | cut -d' ' -f2)" \
  -d '{}'
```

### Получение курса BTC->ETH
```bash
DATA='{"type": "fixed", "fromCcy": "BTC", "toCcy": "ETH", "direction": "from", "amount": 0.1}'
SIGNATURE=$(echo -n "$DATA" | openssl dgst -sha256 -hmac "CUuJ5jIspDOYmEsu5gr11l4RuAjacMGgDJ7TzmUq" | cut -d' ' -f2)

curl -X POST "https://work-1-yiasrhcqtcuxuryd.prod-runtime.all-hands.dev/api/v2/price" \
  -H "Content-Type: application/json; charset=UTF-8" \
  -H "X-API-KEY: WTyKYfiWHx4ayHfhDY5mEVXkI6eFYv418whIrPiQ" \
  -H "X-API-SIGN: $SIGNATURE" \
  -d "$DATA"
```

## 🆘 Устранение неполадок

### Ошибка 401: Missing headers
- Убедитесь, что добавили оба заголовка: X-API-KEY и X-API-SIGN

### Ошибка 401: Invalid signature
- Проверьте, что не сортируете ключи в JSON
- Убедитесь в правильном формате JSON (с пробелами)
- Проверьте API Secret

### Ошибка 429: Rate limit exceeded
- Подождите минуту и повторите запрос
- Используйте меньше запросов в минуту

## 📚 Дополнительные ресурсы

- **Swagger UI**: https://work-1-yiasrhcqtcuxuryd.prod-runtime.all-hands.dev/docs
- **ReDoc**: https://work-1-yiasrhcqtcuxuryd.prod-runtime.all-hands.dev/redoc
- **Готовый клиент**: `/examples/client_example.py`
- **Тесты**: `/test_api.py`