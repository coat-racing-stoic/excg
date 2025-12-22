/**
 * Crypto Exchange API Client - JavaScript/Node.js Example
 * 
 * This example demonstrates how to interact with the Crypto Exchange Backend API
 * using JavaScript/Node.js.
 * 
 * Requirements:
 *   npm install axios crypto
 * 
 * Usage:
 *   node client_javascript.js
 */

const axios = require('axios');
const crypto = require('crypto');

// Configuration
const CONFIG = {
    baseUrl: process.env.API_BASE_URL || 'http://localhost:12000',
    apiKey: process.env.API_KEY || 'YOUR_API_KEY',
    apiSecret: process.env.API_SECRET || 'YOUR_API_SECRET'
};

/**
 * Create HMAC-SHA256 signature for request body
 * @param {string} body - JSON string of request body
 * @returns {string} - Hex-encoded signature
 */
function createSignature(body) {
    return crypto
        .createHmac('sha256', CONFIG.apiSecret)
        .update(body)
        .digest('hex');
}

/**
 * Make authenticated API request
 * @param {string} endpoint - API endpoint path
 * @param {object} data - Request body data
 * @returns {Promise<object>} - API response
 */
async function makeRequest(endpoint, data = {}) {
    // Serialize body with consistent formatting (sorted keys, no spaces)
    const body = JSON.stringify(data, Object.keys(data).sort());
    const signature = createSignature(body);
    
    const headers = {
        'Content-Type': 'application/json',
        'X-API-KEY': CONFIG.apiKey,
        'X-API-SIGN': signature
    };
    
    try {
        const response = await axios.post(`${CONFIG.baseUrl}${endpoint}`, data, { headers });
        return response.data;
    } catch (error) {
        if (error.response) {
            return error.response.data;
        }
        throw error;
    }
}

/**
 * Make unauthenticated GET request
 * @param {string} endpoint - API endpoint path
 * @returns {Promise<object>} - API response
 */
async function makeGetRequest(endpoint) {
    try {
        const response = await axios.get(`${CONFIG.baseUrl}${endpoint}`);
        return response.data;
    } catch (error) {
        if (error.response) {
            return error.response.data;
        }
        throw error;
    }
}

// ============================================================================
// API Methods
// ============================================================================

/**
 * Check API health status
 */
async function healthCheck() {
    return makeGetRequest('/health');
}

/**
 * Get list of supported currencies
 */
async function getCurrencies() {
    return makeRequest('/api/v2/ccies', {});
}

/**
 * Get exchange rate for currency pair
 * @param {string} fromCcy - Source currency code
 * @param {string} toCcy - Target currency code
 * @param {number} amount - Amount to exchange
 * @param {string} direction - 'from' or 'to'
 * @param {string} type - 'fixed' or 'float'
 */
async function getExchangeRate(fromCcy, toCcy, amount, direction = 'from', type = 'fixed') {
    return makeRequest('/api/v2/price', {
        fromCcy,
        toCcy,
        amount,
        direction,
        type
    });
}

/**
 * Create exchange order
 * @param {string} fromCcy - Source currency code
 * @param {string} toCcy - Target currency code
 * @param {number} amount - Amount to exchange
 * @param {string} toAddress - Destination wallet address
 * @param {string} direction - 'from' or 'to'
 * @param {string} type - 'fixed' or 'float'
 */
async function createOrder(fromCcy, toCcy, amount, toAddress, direction = 'from', type = 'fixed') {
    return makeRequest('/api/v2/create', {
        fromCcy,
        toCcy,
        amount,
        toAddress,
        direction,
        type
    });
}

/**
 * Get order status
 * @param {string} orderId - Order ID
 * @param {string} token - Order token
 */
async function getOrderStatus(orderId, token) {
    return makeRequest('/api/v2/order', {
        id: orderId,
        token
    });
}

/**
 * Handle emergency situation
 * @param {string} orderId - Order ID
 * @param {string} token - Order token
 * @param {string} choice - Action choice (EXCHANGE, REFUND)
 * @param {string} address - Address for refund (optional)
 */
async function handleEmergency(orderId, token, choice, address = null) {
    const data = { id: orderId, token, choice };
    if (address) {
        data.address = address;
    }
    return makeRequest('/api/v2/emergency', data);
}

/**
 * Subscribe to email notifications
 * @param {string} orderId - Order ID
 * @param {string} token - Order token
 * @param {string} email - Email address
 */
async function setEmailNotification(orderId, token, email) {
    return makeRequest('/api/v2/setEmail', {
        id: orderId,
        token,
        email
    });
}

/**
 * Get QR code for deposit address
 * @param {string} orderId - Order ID
 * @param {string} token - Order token
 */
async function getQRCode(orderId, token) {
    return makeRequest('/api/v2/qr', {
        id: orderId,
        token
    });
}

// ============================================================================
// Example Usage
// ============================================================================

async function main() {
    console.log('=== Crypto Exchange API - JavaScript Client ===\n');
    
    // 1. Health Check
    console.log('1. Health Check:');
    const health = await healthCheck();
    console.log(JSON.stringify(health, null, 2));
    console.log();
    
    // 2. Get Currencies
    console.log('2. Get Currencies:');
    const currencies = await getCurrencies();
    if (currencies.code === 0 && currencies.data) {
        console.log(`Found ${currencies.data.length} currencies`);
        console.log('First 5:', currencies.data.slice(0, 5).map(c => c.code).join(', '));
    } else {
        console.log('Response:', JSON.stringify(currencies, null, 2));
    }
    console.log();
    
    // 3. Get Exchange Rate
    console.log('3. Get Exchange Rate (BTC -> ETH):');
    const rate = await getExchangeRate('BTC', 'ETH', 0.1, 'from', 'fixed');
    console.log(JSON.stringify(rate, null, 2));
    console.log();
    
    // 4. Example: Create Order (commented out to avoid actual order creation)
    /*
    console.log('4. Create Order:');
    const order = await createOrder(
        'BTC',
        'ETH',
        0.1,
        '0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6',
        'from',
        'fixed'
    );
    console.log(JSON.stringify(order, null, 2));
    
    if (order.code === 0 && order.data) {
        const { id, token } = order.data;
        
        // Get order status
        const status = await getOrderStatus(id, token);
        console.log('Order Status:', JSON.stringify(status, null, 2));
        
        // Set email notification
        const emailResult = await setEmailNotification(id, token, 'user@example.com');
        console.log('Email Notification:', JSON.stringify(emailResult, null, 2));
    }
    */
    
    console.log('=== Done ===');
}

// Run if executed directly
if (require.main === module) {
    main().catch(console.error);
}

// Export functions for use as module
module.exports = {
    healthCheck,
    getCurrencies,
    getExchangeRate,
    createOrder,
    getOrderStatus,
    handleEmergency,
    setEmailNotification,
    getQRCode,
    createSignature,
    makeRequest
};
