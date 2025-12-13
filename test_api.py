#!/usr/bin/env python3
"""
Тестирование API с реальными ключами
"""

import requests
import json
import hmac
import hashlib

# Настройки
BASE_URL = "http://localhost:12000"
API_KEY = "WTyKYfiWHx4ayHfhDY5mEVXkI6eFYv418whIrPiQ"
API_SECRET = "CUuJ5jIspDOYmEsu5gr11l4RuAjacMGgDJ7TzmUq"

def create_signature(data, api_secret):
    """Создание HMAC-SHA256 подписи"""
    json_str = json.dumps(data, separators=(',', ':'), sort_keys=True)
    return hmac.new(
        api_secret.encode('utf-8'),
        json_str.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

def make_authenticated_request(endpoint, data):
    """Выполнение аутентифицированного запроса"""
    url = f"{BASE_URL}{endpoint}"
    
    # Создаем JSON строку так же, как requests (без сортировки ключей!)
    json_data = json.dumps(data, separators=(', ', ': '))
    signature = hmac.new(
        API_SECRET.encode('utf-8'),
        json_data.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    headers = {
        'Content-Type': 'application/json; charset=UTF-8',
        'X-API-KEY': API_KEY,
        'X-API-SIGN': signature
    }
    

    
    response = requests.post(url, headers=headers, json=data)
    return response

def test_health():
    """Тест health check"""
    print("=== Testing Health Check ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_currencies():
    """Тест получения списка валют"""
    print("=== Testing Get Currencies ===")
    response = make_authenticated_request('/api/v2/ccies', {})
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Response code: {data.get('code')}")
        print(f"Message: {data.get('msg')}")
        if data.get('data'):
            print(f"Found {len(data['data'])} currencies")
            print("First 3 currencies:")
            for currency in data['data'][:3]:
                print(f"  {currency['code']} - {currency['name']}")
    else:
        print(f"Error: {response.text}")
    print()

def test_exchange_rate():
    """Тест получения курса обмена"""
    print("=== Testing Get Exchange Rate ===")
    data = {
        "type": "fixed",
        "fromCcy": "BTC",
        "toCcy": "ETH",
        "direction": "from",
        "amount": 0.1
    }
    
    response = make_authenticated_request('/api/v2/price', data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Response code: {result.get('code')}")
        print(f"Message: {result.get('msg')}")
        if result.get('data'):
            exchange_data = result['data']['exchange_rate']
            print(f"From: {exchange_data['from_rate']['amount']} {exchange_data['from_rate']['code']}")
            print(f"To: {exchange_data['to_rate']['amount']} {exchange_data['to_rate']['code']}")
            print(f"Rate: {exchange_data['from_rate']['rate']}")
    else:
        print(f"Error: {response.text}")
    print()

def test_xml_rates():
    """Тест XML курсов"""
    print("=== Testing XML Rates ===")
    
    # Тест JSON парсинга
    response = requests.get(f"{BASE_URL}/api/rates/fixed")
    print(f"JSON Fixed Rates Status: {response.status_code}")
    
    if response.status_code == 200:
        rates = response.json()
        print(f"Found {len(rates)} fixed rate pairs")
        if rates:
            print("First 3 rates:")
            for rate in rates[:3]:
                print(f"  {rate['from']} -> {rate['to']}: {rate['out']}")
    else:
        print(f"Error: {response.text}")
    print()

def main():
    """Запуск всех тестов"""
    print("=== Crypto Exchange Backend API Tests ===\n")
    
    test_health()
    test_xml_rates()
    test_currencies()
    test_exchange_rate()
    
    print("=== Tests completed ===")

if __name__ == "__main__":
    main()