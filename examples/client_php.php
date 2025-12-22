<?php
/**
 * Crypto Exchange API Client - PHP Example
 * 
 * This example demonstrates how to interact with the Crypto Exchange Backend API
 * using PHP.
 * 
 * Requirements:
 *   - PHP 7.4+
 *   - cURL extension
 * 
 * Usage:
 *   php client_php.php
 */

class CryptoExchangeClient
{
    private string $baseUrl;
    private string $apiKey;
    private string $apiSecret;
    
    public function __construct(
        string $baseUrl = 'http://localhost:12000',
        string $apiKey = '',
        string $apiSecret = ''
    ) {
        $this->baseUrl = rtrim($baseUrl, '/');
        $this->apiKey = $apiKey ?: getenv('API_KEY') ?: 'YOUR_API_KEY';
        $this->apiSecret = $apiSecret ?: getenv('API_SECRET') ?: 'YOUR_API_SECRET';
    }
    
    /**
     * Create HMAC-SHA256 signature for request body
     */
    private function createSignature(string $body): string
    {
        return hash_hmac('sha256', $body, $this->apiSecret);
    }
    
    /**
     * Make authenticated POST request
     */
    private function makeRequest(string $endpoint, array $data = []): array
    {
        // Sort keys and encode JSON without spaces
        ksort($data);
        $body = json_encode($data, JSON_UNESCAPED_SLASHES);
        if ($body === '[]') {
            $body = '{}';
        }
        
        $signature = $this->createSignature($body);
        
        $headers = [
            'Content-Type: application/json',
            'X-API-KEY: ' . $this->apiKey,
            'X-API-SIGN: ' . $signature,
        ];
        
        $ch = curl_init($this->baseUrl . $endpoint);
        curl_setopt_array($ch, [
            CURLOPT_POST => true,
            CURLOPT_POSTFIELDS => $body,
            CURLOPT_HTTPHEADER => $headers,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT => 30,
        ]);
        
        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $error = curl_error($ch);
        curl_close($ch);
        
        if ($error) {
            return ['code' => -1, 'msg' => 'cURL Error: ' . $error, 'data' => null];
        }
        
        return json_decode($response, true) ?: ['code' => -1, 'msg' => 'Invalid JSON response', 'data' => null];
    }
    
    /**
     * Make unauthenticated GET request
     */
    private function makeGetRequest(string $endpoint): array
    {
        $ch = curl_init($this->baseUrl . $endpoint);
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT => 30,
        ]);
        
        $response = curl_exec($ch);
        $error = curl_error($ch);
        curl_close($ch);
        
        if ($error) {
            return ['error' => 'cURL Error: ' . $error];
        }
        
        return json_decode($response, true) ?: ['error' => 'Invalid JSON response'];
    }
    
    // ========================================================================
    // API Methods
    // ========================================================================
    
    /**
     * Check API health status
     */
    public function healthCheck(): array
    {
        return $this->makeGetRequest('/health');
    }
    
    /**
     * Get cache status
     */
    public function getCacheStatus(): array
    {
        return $this->makeGetRequest('/api/cache/status');
    }
    
    /**
     * Get list of supported currencies
     */
    public function getCurrencies(): array
    {
        return $this->makeRequest('/api/v2/ccies', []);
    }
    
    /**
     * Get exchange rate for currency pair
     */
    public function getExchangeRate(
        string $fromCcy,
        string $toCcy,
        float $amount,
        string $direction = 'from',
        string $type = 'fixed'
    ): array {
        return $this->makeRequest('/api/v2/price', [
            'fromCcy' => $fromCcy,
            'toCcy' => $toCcy,
            'amount' => $amount,
            'direction' => $direction,
            'type' => $type,
        ]);
    }
    
    /**
     * Get exchange rate with partner commission
     */
    public function getExchangeRateWithPartner(
        string $fromCcy,
        string $toCcy,
        float $amount,
        string $direction,
        string $type,
        string $refcode,
        float $afftax
    ): array {
        return $this->makeRequest('/api/v2/price', [
            'fromCcy' => $fromCcy,
            'toCcy' => $toCcy,
            'amount' => $amount,
            'direction' => $direction,
            'type' => $type,
            'refcode' => $refcode,
            'afftax' => $afftax,
        ]);
    }
    
    /**
     * Create exchange order
     */
    public function createOrder(
        string $fromCcy,
        string $toCcy,
        float $amount,
        string $toAddress,
        string $direction = 'from',
        string $type = 'fixed'
    ): array {
        return $this->makeRequest('/api/v2/create', [
            'fromCcy' => $fromCcy,
            'toCcy' => $toCcy,
            'amount' => $amount,
            'toAddress' => $toAddress,
            'direction' => $direction,
            'type' => $type,
        ]);
    }
    
    /**
     * Get order status
     */
    public function getOrderStatus(string $orderId, string $token): array
    {
        return $this->makeRequest('/api/v2/order', [
            'id' => $orderId,
            'token' => $token,
        ]);
    }
    
    /**
     * Handle emergency situation
     */
    public function handleEmergency(
        string $orderId,
        string $token,
        string $choice,
        ?string $address = null
    ): array {
        $data = [
            'id' => $orderId,
            'token' => $token,
            'choice' => $choice,
        ];
        
        if ($address !== null) {
            $data['address'] = $address;
        }
        
        return $this->makeRequest('/api/v2/emergency', $data);
    }
    
    /**
     * Subscribe to email notifications
     */
    public function setEmailNotification(string $orderId, string $token, string $email): array
    {
        return $this->makeRequest('/api/v2/setEmail', [
            'id' => $orderId,
            'token' => $token,
            'email' => $email,
        ]);
    }
    
    /**
     * Get QR code for deposit address
     */
    public function getQRCode(string $orderId, string $token): array
    {
        return $this->makeRequest('/api/v2/qr', [
            'id' => $orderId,
            'token' => $token,
        ]);
    }
}

// ============================================================================
// Example Usage
// ============================================================================

function main(): void
{
    echo "=== Crypto Exchange API - PHP Client ===\n\n";
    
    // Create client (uses environment variables or defaults)
    $client = new CryptoExchangeClient(
        getenv('API_BASE_URL') ?: 'http://localhost:12000'
    );
    
    // 1. Health Check
    echo "1. Health Check:\n";
    $health = $client->healthCheck();
    echo json_encode($health, JSON_PRETTY_PRINT) . "\n\n";
    
    // 2. Get Currencies
    echo "2. Get Currencies:\n";
    $currencies = $client->getCurrencies();
    if ($currencies['code'] === 0 && isset($currencies['data'])) {
        $count = count($currencies['data']);
        echo "Found {$count} currencies\n";
        $first5 = array_slice($currencies['data'], 0, 5);
        foreach ($first5 as $currency) {
            echo "  - {$currency['code']}: {$currency['name']}\n";
        }
    } else {
        echo "Response: " . json_encode($currencies, JSON_PRETTY_PRINT) . "\n";
    }
    echo "\n";
    
    // 3. Get Exchange Rate
    echo "3. Get Exchange Rate (BTC -> ETH):\n";
    $rate = $client->getExchangeRate('BTC', 'ETH', 0.1, 'from', 'fixed');
    echo json_encode($rate, JSON_PRETTY_PRINT) . "\n\n";
    
    // 4. Example: Create Order (commented out to avoid actual order creation)
    /*
    echo "4. Create Order:\n";
    $order = $client->createOrder(
        'BTC',
        'ETH',
        0.1,
        '0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6',
        'from',
        'fixed'
    );
    echo json_encode($order, JSON_PRETTY_PRINT) . "\n\n";
    
    if ($order['code'] === 0 && isset($order['data'])) {
        $orderId = $order['data']['id'];
        $token = $order['data']['token'];
        
        // Get order status
        $status = $client->getOrderStatus($orderId, $token);
        echo "Order Status: " . json_encode($status, JSON_PRETTY_PRINT) . "\n\n";
        
        // Set email notification
        $emailResult = $client->setEmailNotification($orderId, $token, 'user@example.com');
        echo "Email Notification: " . json_encode($emailResult, JSON_PRETTY_PRINT) . "\n\n";
    }
    */
    
    echo "=== Done ===\n";
}

// Run if executed directly
if (php_sapi_name() === 'cli' && basename(__FILE__) === basename($argv[0])) {
    main();
}
