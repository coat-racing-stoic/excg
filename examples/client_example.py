#!/usr/bin/env python3
"""
Пример клиента для Crypto Exchange Backend API
"""

import requests
import json
import hmac
import hashlib
from typing import Dict, Any, Optional

class CryptoExchangeClient:
    """Клиент для работы с Crypto Exchange Backend API"""
    
    def __init__(self, base_url: str, api_key: str, api_secret: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.api_secret = api_secret
        self.session = requests.Session()
    
    def _create_signature(self, data: Dict[str, Any]) -> str:
        """Создание HMAC-SHA256 подписи"""
        json_str = json.dumps(data, separators=(', ', ': '))
        return hmac.new(
            self.api_secret.encode('utf-8'),
            json_str.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _make_authenticated_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Выполнение аутентифицированного запроса"""
        url = f"{self.base_url}{endpoint}"
        signature = self._create_signature(data)
        
        headers = {
            'Content-Type': 'application/json; charset=UTF-8',
            'X-API-KEY': self.api_key,
            'X-API-SIGN': signature
        }
        
        response = self.session.post(url, headers=headers, json=data)
        
        if response.status_code == 429:
            print(f"Rate limit exceeded. Headers: {response.headers}")
            return {"error": "Rate limit exceeded", "headers": dict(response.headers)}
        
        try:
            return response.json()
        except ValueError:
            return {"error": f"Invalid JSON response: {response.text}"}
    
    def _make_public_request(self, endpoint: str) -> Any:
        """Выполнение публичного запроса"""
        url = f"{self.base_url}{endpoint}"
        response = self.session.get(url)
        
        if 'xml' in endpoint:
            return response.text
        else:
            return response.json()
    
    def get_currencies(self) -> Dict[str, Any]:
        """Получение списка валют"""
        return self._make_authenticated_request('/api/v2/ccies', {})
    
    def get_exchange_rate(self, from_currency: str, to_currency: str, 
                         amount: float, exchange_type: str = "fixed",
                         direction: str = "from", refcode: Optional[str] = None,
                         afftax: Optional[float] = None) -> Dict[str, Any]:
        """Получение курса обмена"""
        data = {
            "type": exchange_type,
            "fromCcy": from_currency,
            "toCcy": to_currency,
            "direction": direction,
            "amount": amount
        }
        
        if refcode:
            data["refcode"] = refcode
        if afftax:
            data["afftax"] = afftax
        
        return self._make_authenticated_request('/api/v2/price', data)
    
    def create_order(self, from_currency: str, to_currency: str, 
                    amount: float, to_address: str, exchange_type: str = "fixed",
                    direction: str = "from", tag: Optional[str] = None,
                    refcode: Optional[str] = None, afftax: Optional[float] = None) -> Dict[str, Any]:
        """Создание ордера"""
        data = {
            "type": exchange_type,
            "fromCcy": from_currency,
            "toCcy": to_currency,
            "direction": direction,
            "amount": amount,
            "toAddress": to_address
        }
        
        if tag:
            data["tag"] = tag
        if refcode:
            data["refcode"] = refcode
        if afftax:
            data["afftax"] = afftax
        
        return self._make_authenticated_request('/api/v2/create', data)
    
    def get_order_status(self, order_id: str, token: str) -> Dict[str, Any]:
        """Получение статуса ордера"""
        data = {
            "id": order_id,
            "token": token
        }
        return self._make_authenticated_request('/api/v2/order', data)
    
    def handle_emergency(self, order_id: str, token: str, choice: str,
                        address: Optional[str] = None, tag: Optional[str] = None) -> Dict[str, Any]:
        """Обработка аварийной ситуации"""
        data = {
            "id": order_id,
            "token": token,
            "choice": choice
        }
        
        if address:
            data["address"] = address
        if tag:
            data["tag"] = tag
        
        return self._make_authenticated_request('/api/v2/emergency', data)
    
    def set_email(self, order_id: str, token: str, email: str) -> Dict[str, Any]:
        """Установка email для уведомлений"""
        data = {
            "id": order_id,
            "token": token,
            "email": email
        }
        return self._make_authenticated_request('/api/v2/setEmail', data)
    
    def get_qr_codes(self, order_id: str, token: str) -> Dict[str, Any]:
        """Получение QR-кодов"""
        data = {
            "id": order_id,
            "token": token
        }
        return self._make_authenticated_request('/api/v2/qr', data)
    
    def get_fixed_rates_xml(self) -> str:
        """Получение фиксированных курсов в XML"""
        return self._make_public_request('/rates/fixed.xml')
    
    def get_float_rates_xml(self) -> str:
        """Получение плавающих курсов в XML"""
        return self._make_public_request('/rates/float.xml')
    
    def get_fixed_rates_json(self) -> Dict[str, Any]:
        """Получение фиксированных курсов в JSON"""
        return self._make_public_request('/api/rates/fixed')
    
    def get_float_rates_json(self) -> Dict[str, Any]:
        """Получение плавающих курсов в JSON"""
        return self._make_public_request('/api/rates/float')
    
    def health_check(self) -> Dict[str, Any]:
        """Проверка состояния сервиса"""
        return self._make_public_request('/health')

def main():
    """Пример использования клиента"""
    
    # Настройки (замените на ваши реальные данные)
    BASE_URL = "http://localhost:12000"
    API_KEY = "WTyKYfiWHx4ayHfhDY5mEVXkI6eFYv418whIrPiQ"
    API_SECRET = "CUuJ5jIspDOYmEsu5gr11l4RuAjacMGgDJ7TzmUq"
    
    # Создание клиента
    client = CryptoExchangeClient(BASE_URL, API_KEY, API_SECRET)
    
    print("=== Crypto Exchange Backend API Client Example ===\n")
    
    # 1. Проверка состояния сервиса
    print("1. Health Check:")
    health = client.health_check()
    print(json.dumps(health, indent=2))
    print()
    
    # 2. Получение курсов без аутентификации
    print("2. Getting fixed rates (JSON):")
    try:
        fixed_rates = client.get_fixed_rates_json()
        print(f"Found {len(fixed_rates)} fixed rate pairs")
        if fixed_rates:
            print("First 3 rates:")
            for rate in fixed_rates[:3]:
                print(f"  {rate['from']} -> {rate['to']}: {rate['out']}")
    except Exception as e:
        print(f"Error: {e}")
    print()
    
    # 3. Получение списка валют (требует аутентификации)
    print("3. Getting currencies list:")
    try:
        currencies = client.get_currencies()
        if currencies.get('code') == 0:
            print(f"Found {len(currencies['data'])} currencies")
            print("First 5 currencies:")
            for currency in currencies['data'][:5]:
                print(f"  {currency['code']} - {currency['name']}")
        else:
            print(f"Error: {currencies}")
    except Exception as e:
        print(f"Error: {e}")
    print()
    
    # 4. Получение курса обмена
    print("4. Getting exchange rate (BTC -> ETH):")
    try:
        rate = client.get_exchange_rate("BTC", "ETH", 0.1, "fixed", "from")
        if rate.get('code') == 0:
            exchange_data = rate['data']['exchange_rate']
            print(f"From: {exchange_data['from_rate']['amount']} {exchange_data['from_rate']['code']}")
            print(f"To: {exchange_data['to_rate']['amount']} {exchange_data['to_rate']['code']}")
            print(f"Rate: {exchange_data['from_rate']['rate']}")
        else:
            print(f"Error: {rate}")
    except Exception as e:
        print(f"Error: {e}")
    print()
    
    # 5. Получение курса с партнерскими параметрами
    print("5. Getting exchange rate with partner parameters:")
    try:
        rate = client.get_exchange_rate("BTC", "ETH", 0.1, "fixed", "from", 
                                      refcode="DEMO001", afftax=2.5)
        if rate.get('code') == 0:
            if rate['data']['partner_calculation']:
                partner = rate['data']['partner_calculation']
                print(f"Partner code: {partner['refcode']}")
                print(f"Commission: {partner['afftax']}%")
                print(f"Total commission: {partner['total_commission']}")
                print(f"Formula: {partner['formula_used']}")
        else:
            print(f"Error: {rate}")
    except Exception as e:
        print(f"Error: {e}")
    print()
    
    # 6. Создание ордера (закомментировано для безопасности)
    print("6. Creating order (commented out for safety):")
    print("# Uncomment the following lines to create a real order:")
    print("# order = client.create_order('BTC', 'ETH', 0.001, '0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6')")
    print("# print(json.dumps(order, indent=2))")
    print()
    
    print("=== Example completed ===")

if __name__ == "__main__":
    main()