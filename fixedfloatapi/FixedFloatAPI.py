import json
import hashlib
import requests
import hmac
import xml.etree.ElementTree as ET

class FixedFloatApi:
    RESP_OK = 0
    TYPE_FIXED = 'fixed'
    TYPE_FLOAT = 'float'

    def __init__(self, key, secret):
        self.key = key
        self.secret = secret

    def sign(self, data):
        parts = []
        if isinstance(data, dict):
            for key, value in data.items():
                parts.append(f'{key}={value}')
            data = '&'.join(parts)
        return hmac.new(self.secret.encode('utf-8'), data.encode('utf-8'), hashlib.sha256).hexdigest()

    def req(self, method, data):
        url = f'https://ff.io/api/v2/{method}'

        req = json.dumps(data)

        headers = {
            'Content-Type': 'application/json',
            'X-API-KEY': self.key,
            'X-API-SIGN': self.sign(req)
        }

        response = requests.post(url, headers=headers, data=req, verify=True)

        try:
            result = response.json()
        except ValueError:
            raise Exception(f'Invalid JSON response: {response.content}')

        if response.status_code != 200:
            raise Exception(f'Request failed with status {response.status_code}: {result.get("msg", "")}')

        if result['code'] != self.RESP_OK:
            raise Exception(result['msg'], result['code'])

        return result['data']

    def ccies(self):
        return self.req('ccies', {})

    def price(self, data):
        return self.req('price', data)

    def create(self, data):
        return self.req('create', data)

    def order(self, data):
        return self.req('order', data)

    def emergency(self, data):
        return self.req('emergency', data)

    def setEmail(self, data):
        return self.req('setEmail', data)

    def qr(self, data):
        return self.req('qr', data)

    def custom_request(self, method, data):
        return self.req(method, data)

    def xml_req(self, endpoint):
        """
        Make a GET request to XML endpoints (no authentication required)
        
        Args:
            endpoint (str): The XML endpoint path (e.g., 'rates/fixed.xml')
            
        Returns:
            str: Raw XML response content
            
        Raises:
            Exception: If request fails or returns non-200 status
        """
        url = f'https://ff.io/{endpoint}'
        
        response = requests.get(url, verify=True)
        
        if response.status_code != 200:
            raise Exception(f'XML request failed with status {response.status_code}: {response.text}')
        
        return response.text

    def parse_xml_rates(self, xml_content):
        """
        Parse XML rates content into Python data structure
        
        Args:
            xml_content (str): Raw XML content
            
        Returns:
            list: List of rate dictionaries with parsed data
            
        Raises:
            Exception: If XML parsing fails
        """
        try:
            root = ET.fromstring(xml_content)
            rates = []
            
            for item in root.findall('item'):
                rate_data = {}
                for child in item:
                    if child.tag in ['in', 'out', 'amount']:
                        # Convert numeric fields to float
                        try:
                            rate_data[child.tag] = float(child.text) if child.text else 0.0
                        except (ValueError, TypeError):
                            rate_data[child.tag] = 0.0
                    else:
                        # Keep string fields as strings
                        rate_data[child.tag] = child.text if child.text else ''
                
                rates.append(rate_data)
            
            return rates
            
        except ET.ParseError as e:
            raise Exception(f'Failed to parse XML: {e}')

    def get_rates_fixed_xml(self, parse=True):
        """
        Get fixed exchange rates in XML format
        
        This method doesn't require authentication and provides all available
        fixed exchange rates. Recommended for mass operations with local caching (TTL 5-10 minutes).
        
        Args:
            parse (bool): If True, parse XML to Python dict. If False, return raw XML string.
            
        Returns:
            list or str: Parsed rates data (if parse=True) or raw XML string (if parse=False)
            
        Raises:
            Exception: If request fails or XML parsing fails (when parse=True)
        """
        xml_content = self.xml_req('rates/fixed.xml')
        
        if parse:
            return self.parse_xml_rates(xml_content)
        else:
            return xml_content

    def get_rates_float_xml(self, parse=True):
        """
        Get floating exchange rates in XML format
        
        This method doesn't require authentication and provides all available
        floating exchange rates. Recommended for mass operations with local caching (TTL 5-10 minutes).
        
        Args:
            parse (bool): If True, parse XML to Python dict. If False, return raw XML string.
            
        Returns:
            list or str: Parsed rates data (if parse=True) or raw XML string (if parse=False)
            
        Raises:
            Exception: If request fails or XML parsing fails (when parse=True)
        """
        xml_content = self.xml_req('rates/float.xml')
        
        if parse:
            return self.parse_xml_rates(xml_content)
        else:
            return xml_content
