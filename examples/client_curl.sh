#!/bin/bash
#
# Crypto Exchange API Client - cURL Examples
#
# This script demonstrates how to interact with the Crypto Exchange Backend API
# using cURL commands.
#
# Usage:
#   chmod +x client_curl.sh
#   ./client_curl.sh
#
# Or source it to use individual functions:
#   source client_curl.sh
#   get_currencies

# Configuration
BASE_URL="${API_BASE_URL:-http://localhost:12000}"
API_KEY="${API_KEY:-YOUR_API_KEY}"
API_SECRET="${API_SECRET:-YOUR_API_SECRET}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ============================================================================
# Helper Functions
# ============================================================================

# Create HMAC-SHA256 signature
create_signature() {
    local body="$1"
    echo -n "$body" | openssl dgst -sha256 -hmac "$API_SECRET" | cut -d' ' -f2
}

# Make authenticated POST request
make_request() {
    local endpoint="$1"
    local body="$2"
    local signature=$(create_signature "$body")
    
    curl -s -X POST "${BASE_URL}${endpoint}" \
        -H "Content-Type: application/json" \
        -H "X-API-KEY: ${API_KEY}" \
        -H "X-API-SIGN: ${signature}" \
        -d "$body"
}

# Make unauthenticated GET request
make_get_request() {
    local endpoint="$1"
    curl -s "${BASE_URL}${endpoint}"
}

# Pretty print JSON
pretty_json() {
    if command -v jq &> /dev/null; then
        jq '.'
    elif command -v python3 &> /dev/null; then
        python3 -m json.tool
    else
        cat
    fi
}

# ============================================================================
# API Functions
# ============================================================================

# Health check
health_check() {
    echo -e "${GREEN}=== Health Check ===${NC}"
    make_get_request "/health" | pretty_json
    echo
}

# Get cache status
cache_status() {
    echo -e "${GREEN}=== Cache Status ===${NC}"
    make_get_request "/api/cache/status" | pretty_json
    echo
}

# Get currencies
get_currencies() {
    echo -e "${GREEN}=== Get Currencies ===${NC}"
    make_request "/api/v2/ccies" "{}" | pretty_json
    echo
}

# Get exchange rate
# Usage: get_exchange_rate BTC ETH 0.1 from fixed
get_exchange_rate() {
    local from_ccy="${1:-BTC}"
    local to_ccy="${2:-ETH}"
    local amount="${3:-0.1}"
    local direction="${4:-from}"
    local type="${5:-fixed}"
    
    echo -e "${GREEN}=== Get Exchange Rate (${from_ccy} -> ${to_ccy}) ===${NC}"
    
    # Build JSON with sorted keys
    local body=$(cat <<EOF
{"amount":${amount},"direction":"${direction}","fromCcy":"${from_ccy}","toCcy":"${to_ccy}","type":"${type}"}
EOF
)
    
    make_request "/api/v2/price" "$body" | pretty_json
    echo
}

# Get exchange rate with partner commission
# Usage: get_exchange_rate_partner BTC ETH 0.1 from fixed PARTNER001 2.5
get_exchange_rate_partner() {
    local from_ccy="${1:-BTC}"
    local to_ccy="${2:-ETH}"
    local amount="${3:-0.1}"
    local direction="${4:-from}"
    local type="${5:-fixed}"
    local refcode="${6:-PARTNER001}"
    local afftax="${7:-2.5}"
    
    echo -e "${GREEN}=== Get Exchange Rate with Partner ===${NC}"
    
    local body=$(cat <<EOF
{"afftax":${afftax},"amount":${amount},"direction":"${direction}","fromCcy":"${from_ccy}","refcode":"${refcode}","toCcy":"${to_ccy}","type":"${type}"}
EOF
)
    
    make_request "/api/v2/price" "$body" | pretty_json
    echo
}

# Create order
# Usage: create_order BTC ETH 0.1 0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6 from fixed
create_order() {
    local from_ccy="${1:-BTC}"
    local to_ccy="${2:-ETH}"
    local amount="${3:-0.1}"
    local to_address="${4}"
    local direction="${5:-from}"
    local type="${6:-fixed}"
    
    if [ -z "$to_address" ]; then
        echo -e "${RED}Error: toAddress is required${NC}"
        return 1
    fi
    
    echo -e "${GREEN}=== Create Order ===${NC}"
    
    local body=$(cat <<EOF
{"amount":${amount},"direction":"${direction}","fromCcy":"${from_ccy}","toAddress":"${to_address}","toCcy":"${to_ccy}","type":"${type}"}
EOF
)
    
    make_request "/api/v2/create" "$body" | pretty_json
    echo
}

# Get order status
# Usage: get_order_status ORDER_ID ORDER_TOKEN
get_order_status() {
    local order_id="$1"
    local token="$2"
    
    if [ -z "$order_id" ] || [ -z "$token" ]; then
        echo -e "${RED}Error: order_id and token are required${NC}"
        return 1
    fi
    
    echo -e "${GREEN}=== Get Order Status ===${NC}"
    
    local body=$(cat <<EOF
{"id":"${order_id}","token":"${token}"}
EOF
)
    
    make_request "/api/v2/order" "$body" | pretty_json
    echo
}

# Handle emergency
# Usage: handle_emergency ORDER_ID ORDER_TOKEN EXCHANGE [ADDRESS]
handle_emergency() {
    local order_id="$1"
    local token="$2"
    local choice="$3"
    local address="$4"
    
    if [ -z "$order_id" ] || [ -z "$token" ] || [ -z "$choice" ]; then
        echo -e "${RED}Error: order_id, token, and choice are required${NC}"
        return 1
    fi
    
    echo -e "${GREEN}=== Handle Emergency ===${NC}"
    
    local body
    if [ -n "$address" ]; then
        body=$(cat <<EOF
{"address":"${address}","choice":"${choice}","id":"${order_id}","token":"${token}"}
EOF
)
    else
        body=$(cat <<EOF
{"choice":"${choice}","id":"${order_id}","token":"${token}"}
EOF
)
    fi
    
    make_request "/api/v2/emergency" "$body" | pretty_json
    echo
}

# Set email notification
# Usage: set_email ORDER_ID ORDER_TOKEN user@example.com
set_email() {
    local order_id="$1"
    local token="$2"
    local email="$3"
    
    if [ -z "$order_id" ] || [ -z "$token" ] || [ -z "$email" ]; then
        echo -e "${RED}Error: order_id, token, and email are required${NC}"
        return 1
    fi
    
    echo -e "${GREEN}=== Set Email Notification ===${NC}"
    
    local body=$(cat <<EOF
{"email":"${email}","id":"${order_id}","token":"${token}"}
EOF
)
    
    make_request "/api/v2/setEmail" "$body" | pretty_json
    echo
}

# Get QR code
# Usage: get_qr ORDER_ID ORDER_TOKEN
get_qr() {
    local order_id="$1"
    local token="$2"
    
    if [ -z "$order_id" ] || [ -z "$token" ]; then
        echo -e "${RED}Error: order_id and token are required${NC}"
        return 1
    fi
    
    echo -e "${GREEN}=== Get QR Code ===${NC}"
    
    local body=$(cat <<EOF
{"id":"${order_id}","token":"${token}"}
EOF
)
    
    make_request "/api/v2/qr" "$body" | pretty_json
    echo
}

# Get fixed rates (XML)
get_fixed_rates_xml() {
    echo -e "${GREEN}=== Fixed Rates (XML) ===${NC}"
    make_get_request "/rates/fixed.xml" | head -50
    echo -e "\n... (truncated)\n"
}

# Get float rates (XML)
get_float_rates_xml() {
    echo -e "${GREEN}=== Float Rates (XML) ===${NC}"
    make_get_request "/rates/float.xml" | head -50
    echo -e "\n... (truncated)\n"
}

# Get fixed rates (JSON)
get_fixed_rates_json() {
    echo -e "${GREEN}=== Fixed Rates (JSON) ===${NC}"
    make_get_request "/api/rates/fixed" | pretty_json | head -100
    echo -e "\n... (truncated)\n"
}

# Get float rates (JSON)
get_float_rates_json() {
    echo -e "${GREEN}=== Float Rates (JSON) ===${NC}"
    make_get_request "/api/rates/float" | pretty_json | head -100
    echo -e "\n... (truncated)\n"
}

# ============================================================================
# Main Demo
# ============================================================================

demo() {
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}  Crypto Exchange API - cURL Demo${NC}"
    echo -e "${YELLOW}========================================${NC}"
    echo
    echo "Base URL: ${BASE_URL}"
    echo "API Key: ${API_KEY:0:10}..."
    echo
    
    # 1. Health Check
    health_check
    
    # 2. Get Currencies
    get_currencies
    
    # 3. Get Exchange Rate
    get_exchange_rate BTC ETH 0.1 from fixed
    
    # 4. Get Exchange Rate (USDT -> BTC)
    get_exchange_rate USDTTRC BTC 1000 from float
    
    echo -e "${YELLOW}=== Demo Complete ===${NC}"
}

# Show help
show_help() {
    echo "Crypto Exchange API - cURL Client"
    echo
    echo "Usage: $0 [command] [args...]"
    echo
    echo "Commands:"
    echo "  demo                    Run demo with all basic operations"
    echo "  health                  Health check"
    echo "  cache                   Cache status"
    echo "  currencies              Get list of currencies"
    echo "  rate FROM TO AMOUNT     Get exchange rate"
    echo "  create FROM TO AMOUNT ADDRESS  Create order"
    echo "  status ID TOKEN         Get order status"
    echo "  email ID TOKEN EMAIL    Set email notification"
    echo "  qr ID TOKEN             Get QR code"
    echo "  fixed-xml               Get fixed rates (XML)"
    echo "  float-xml               Get float rates (XML)"
    echo "  fixed-json              Get fixed rates (JSON)"
    echo "  float-json              Get float rates (JSON)"
    echo
    echo "Environment variables:"
    echo "  API_BASE_URL   Base URL (default: http://localhost:12000)"
    echo "  API_KEY        API key"
    echo "  API_SECRET     API secret"
}

# Main entry point
main() {
    case "${1:-demo}" in
        demo)
            demo
            ;;
        health)
            health_check
            ;;
        cache)
            cache_status
            ;;
        currencies)
            get_currencies
            ;;
        rate)
            get_exchange_rate "$2" "$3" "$4" "${5:-from}" "${6:-fixed}"
            ;;
        create)
            create_order "$2" "$3" "$4" "$5" "${6:-from}" "${7:-fixed}"
            ;;
        status)
            get_order_status "$2" "$3"
            ;;
        email)
            set_email "$2" "$3" "$4"
            ;;
        qr)
            get_qr "$2" "$3"
            ;;
        fixed-xml)
            get_fixed_rates_xml
            ;;
        float-xml)
            get_float_rates_xml
            ;;
        fixed-json)
            get_fixed_rates_json
            ;;
        float-json)
            get_float_rates_json
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
