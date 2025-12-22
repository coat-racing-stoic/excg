# API Documentation

This directory contains API documentation and specifications for the Crypto Exchange Backend.

## Files

| File | Description |
|------|-------------|
| `openapi.json` | OpenAPI 3.1 specification in JSON format |
| `openapi.yaml` | OpenAPI 3.1 specification in YAML format |
| `postman_collection.json` | Postman collection for API testing |

## OpenAPI Specification

The OpenAPI specification describes all API endpoints, request/response schemas, and authentication requirements.

### Using with Swagger UI

The API server includes built-in Swagger UI documentation:
- **Swagger UI**: http://localhost:12000/docs
- **ReDoc**: http://localhost:12000/redoc

### Using with External Tools

You can import `openapi.json` or `openapi.yaml` into:
- [Swagger Editor](https://editor.swagger.io/)
- [Stoplight Studio](https://stoplight.io/studio)
- [Insomnia](https://insomnia.rest/)
- [Postman](https://www.postman.com/) (via Import)

### Generating Client SDKs

Use [OpenAPI Generator](https://openapi-generator.tech/) to generate client libraries:

```bash
# Install OpenAPI Generator
npm install @openapitools/openapi-generator-cli -g

# Generate Python client
openapi-generator-cli generate -i docs/openapi.json -g python -o ./generated/python-client

# Generate TypeScript client
openapi-generator-cli generate -i docs/openapi.json -g typescript-axios -o ./generated/ts-client

# Generate Go client
openapi-generator-cli generate -i docs/openapi.json -g go -o ./generated/go-client
```

## Postman Collection

The Postman collection includes:
- All API endpoints with example requests
- Pre-request scripts for automatic signature generation
- Environment variables for easy configuration
- Example responses

### Importing into Postman

1. Open Postman
2. Click **Import** button
3. Select `postman_collection.json`
4. Configure variables:
   - `base_url`: Your API server URL (e.g., `http://localhost:12000`)
   - `api_key`: Your API key
   - `api_secret`: Your API secret

### Using the Collection

1. Select an endpoint from the collection
2. The pre-request script will automatically generate the signature
3. Click **Send** to make the request

## API Overview

### Base URL

```
http://localhost:12000
```

### Authentication

Authenticated endpoints require:
- `X-API-KEY`: Your API key
- `X-API-SIGN`: HMAC-SHA256 signature of request body

### Endpoints

#### Public Endpoints (No Auth)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/api/cache/status` | Cache status |
| GET | `/rates/fixed.xml` | Fixed rates (XML) |
| GET | `/rates/float.xml` | Float rates (XML) |
| GET | `/api/rates/fixed` | Fixed rates (JSON) |
| GET | `/api/rates/float` | Float rates (JSON) |

#### Authenticated Endpoints

| Method | Path | Weight | Description |
|--------|------|--------|-------------|
| POST | `/api/v2/ccies` | 1 | Get currencies |
| POST | `/api/v2/price` | 1 | Get exchange rate |
| POST | `/api/v2/create` | 50 | Create order |
| POST | `/api/v2/order` | 1 | Get order status |
| POST | `/api/v2/emergency` | 1 | Handle emergency |
| POST | `/api/v2/setEmail` | 1 | Set email notification |
| POST | `/api/v2/qr` | 1 | Get QR code |

### Rate Limiting

- **Limit**: 250 weight units per minute
- **Create order**: 50 units
- **Other requests**: 1 unit

### Response Format

```json
{
  "code": 0,
  "msg": "Success",
  "data": { ... }
}
```

### Error Codes

| Code | Description |
|------|-------------|
| 0 | Success |
| 400 | Validation error |
| 401 | Authentication error |
| 404 | Not found |
| 429 | Rate limit exceeded |
| 500 | Internal server error |
| 502 | External API error |

## Regenerating Documentation

To regenerate the OpenAPI specification from the running server:

```python
import json
import yaml
from main import app

# Get OpenAPI schema
schema = app.openapi()

# Save as JSON
with open('docs/openapi.json', 'w') as f:
    json.dump(schema, f, indent=2)

# Save as YAML
with open('docs/openapi.yaml', 'w') as f:
    yaml.dump(schema, f, default_flow_style=False)
```

Or use the `/openapi.json` endpoint:

```bash
curl http://localhost:12000/openapi.json > docs/openapi.json
```
