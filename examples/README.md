# API Client Examples

This directory contains example clients for the Crypto Exchange Backend API in various programming languages.

## Available Examples

| File | Language | Description |
|------|----------|-------------|
| `client_example.py` | Python | Full-featured Python client with all API methods |
| `client_javascript.js` | JavaScript/Node.js | Node.js client using axios |
| `client_go.go` | Go | Go client with typed requests/responses |
| `client_php.php` | PHP | PHP client using cURL |
| `client_curl.sh` | Bash/cURL | Shell script with cURL commands |

## Quick Start

### Python

```bash
# Install dependencies
pip install requests

# Set environment variables
export API_KEY="your_api_key"
export API_SECRET="your_api_secret"
export API_BASE_URL="http://localhost:12000"

# Run
python client_example.py
```

### JavaScript/Node.js

```bash
# Install dependencies
npm install axios

# Set environment variables
export API_KEY="your_api_key"
export API_SECRET="your_api_secret"
export API_BASE_URL="http://localhost:12000"

# Run
node client_javascript.js
```

### Go

```bash
# Set environment variables
export API_KEY="your_api_key"
export API_SECRET="your_api_secret"
export API_BASE_URL="http://localhost:12000"

# Run directly
go run client_go.go

# Or build and run
go build -o client client_go.go
./client
```

### PHP

```bash
# Set environment variables
export API_KEY="your_api_key"
export API_SECRET="your_api_secret"
export API_BASE_URL="http://localhost:12000"

# Run
php client_php.php
```

### cURL/Bash

```bash
# Make executable
chmod +x client_curl.sh

# Set environment variables
export API_KEY="your_api_key"
export API_SECRET="your_api_secret"
export API_BASE_URL="http://localhost:12000"

# Run demo
./client_curl.sh demo

# Or use individual commands
./client_curl.sh health
./client_curl.sh currencies
./client_curl.sh rate BTC ETH 0.1
```

## Authentication

All authenticated endpoints require two headers:

- `X-API-KEY`: Your API key
- `X-API-SIGN`: HMAC-SHA256 signature of the request body

### Signature Generation

The signature is created by:
1. Serializing the request body as JSON (with sorted keys, no extra spaces)
2. Computing HMAC-SHA256 using your API secret
3. Encoding the result as hexadecimal

Example in Python:
```python
import hmac
import hashlib
import json

def create_signature(api_secret: str, data: dict) -> str:
    body = json.dumps(data, separators=(',', ':'), sort_keys=True)
    return hmac.new(
        api_secret.encode('utf-8'),
        body.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
```

## API Endpoints

### Public (No Authentication)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/api/cache/status` | Cache status |
| GET | `/rates/fixed.xml` | Fixed rates (XML) |
| GET | `/rates/float.xml` | Float rates (XML) |
| GET | `/api/rates/fixed` | Fixed rates (JSON) |
| GET | `/api/rates/float` | Float rates (JSON) |

### Authenticated

| Method | Endpoint | Weight | Description |
|--------|----------|--------|-------------|
| POST | `/api/v2/ccies` | 1 | Get currencies |
| POST | `/api/v2/price` | 1 | Get exchange rate |
| POST | `/api/v2/create` | 50 | Create order |
| POST | `/api/v2/order` | 1 | Get order status |
| POST | `/api/v2/emergency` | 1 | Handle emergency |
| POST | `/api/v2/setEmail` | 1 | Set email notification |
| POST | `/api/v2/qr` | 1 | Get QR code |

## Rate Limiting

- **Total limit**: 250 weight units per minute
- **Create order**: 50 units
- **Other requests**: 1 unit

Rate limit headers in response:
- `X-RateLimit-Limit`: Total limit
- `X-RateLimit-Remaining`: Remaining units
- `X-RateLimit-Reset`: Reset timestamp

## Error Handling

All API responses follow this format:

```json
{
  "code": 0,
  "msg": "Success",
  "data": { ... }
}
```

Error codes:
- `0`: Success
- `400`: Validation error
- `401`: Authentication error
- `404`: Not found
- `429`: Rate limit exceeded
- `500`: Internal server error
- `502`: External API error

## Support

- **API Documentation**: http://localhost:12000/docs (Swagger UI)
- **Alternative Docs**: http://localhost:12000/redoc (ReDoc)
- **OpenAPI Spec**: See `docs/openapi.json` or `docs/openapi.yaml`
- **Postman Collection**: See `docs/postman_collection.json`
