# Changelog

## [1.1.0] - 2024-12-13

### Added
- **XML Rate Methods**: Complete implementation of FixedFloat XML endpoints
  - `get_rates_fixed_xml()` - Get fixed exchange rates without authentication
  - `get_rates_float_xml()` - Get floating exchange rates without authentication
  - `xml_req()` - Helper method for XML GET requests
  - `parse_xml_rates()` - XML parser with error handling
- **Flexible Output**: Support for both parsed Python data and raw XML
- **Complete Documentation**: Updated README with XML methods examples and best practices
- **100% API Coverage**: All 9 FixedFloat API methods now implemented

### Changed
- Version bumped to 1.1.0
- Enhanced package description to mention XML rate methods
- Added comprehensive examples for XML methods usage

### Technical Details
- No new dependencies (uses built-in `xml.etree.ElementTree`)
- XML methods don't require API authentication
- Perfect for mass operations with local caching (TTL 5-10 minutes)
- No rate limiting on XML endpoints
- Robust error handling for XML parsing and HTTP requests

### Usage Examples
```python
# Get parsed exchange rates
api = FixedFloatApi(key=None, secret=None)
rates = api.get_rates_fixed_xml(parse=True)

# Get raw XML for custom processing  
raw_xml = api.get_rates_fixed_xml(parse=False)
```

### API Coverage
- ✅ POST /api/v2/ccies (ccies)
- ✅ POST /api/v2/price (price)
- ✅ POST /api/v2/create (create)
- ✅ POST /api/v2/order (order)
- ✅ POST /api/v2/emergency (emergency)
- ✅ POST /api/v2/setEmail (setEmail)
- ✅ POST /api/v2/qr (qr)
- ✅ GET /rates/fixed.xml (get_rates_fixed_xml) **NEW**
- ✅ GET /rates/float.xml (get_rates_float_xml) **NEW**

## [1.0.3] - Previous Release
- Basic API methods implementation
- Authentication and request signing
- Error handling for API responses