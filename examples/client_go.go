/*
Crypto Exchange API Client - Go Example

This example demonstrates how to interact with the Crypto Exchange Backend API
using Go.

Usage:
  go run client_go.go

Or build and run:
  go build -o client client_go.go
  ./client
*/

package main

import (
	"bytes"
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"sort"
	"time"
)

// Config holds API configuration
type Config struct {
	BaseURL   string
	APIKey    string
	APISecret string
}

// Client is the API client
type Client struct {
	config     Config
	httpClient *http.Client
}

// BaseResponse represents the standard API response
type BaseResponse struct {
	Code int             `json:"code"`
	Msg  string          `json:"msg"`
	Data json.RawMessage `json:"data,omitempty"`
}

// HealthResponse represents health check response
type HealthResponse struct {
	Status    string `json:"status"`
	Timestamp string `json:"timestamp"`
	Version   string `json:"version"`
}

// Currency represents a cryptocurrency
type Currency struct {
	Code    string `json:"code"`
	Name    string `json:"name"`
	Network string `json:"network"`
	Coin    string `json:"coin"`
}

// PriceRequest represents exchange rate request
type PriceRequest struct {
	FromCcy   string  `json:"fromCcy"`
	ToCcy     string  `json:"toCcy"`
	Amount    float64 `json:"amount"`
	Direction string  `json:"direction"`
	Type      string  `json:"type"`
}

// CreateOrderRequest represents order creation request
type CreateOrderRequest struct {
	FromCcy   string  `json:"fromCcy"`
	ToCcy     string  `json:"toCcy"`
	Amount    float64 `json:"amount"`
	ToAddress string  `json:"toAddress"`
	Direction string  `json:"direction"`
	Type      string  `json:"type"`
}

// OrderRequest represents order status request
type OrderRequest struct {
	ID    string `json:"id"`
	Token string `json:"token"`
}

// NewClient creates a new API client
func NewClient(config Config) *Client {
	return &Client{
		config: config,
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

// NewClientFromEnv creates a client from environment variables
func NewClientFromEnv() *Client {
	config := Config{
		BaseURL:   getEnv("API_BASE_URL", "http://localhost:12000"),
		APIKey:    getEnv("API_KEY", "YOUR_API_KEY"),
		APISecret: getEnv("API_SECRET", "YOUR_API_SECRET"),
	}
	return NewClient(config)
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

// createSignature generates HMAC-SHA256 signature
func (c *Client) createSignature(body []byte) string {
	h := hmac.New(sha256.New, []byte(c.config.APISecret))
	h.Write(body)
	return hex.EncodeToString(h.Sum(nil))
}

// sortedJSON returns JSON with sorted keys
func sortedJSON(data interface{}) ([]byte, error) {
	// First marshal to get the map
	jsonBytes, err := json.Marshal(data)
	if err != nil {
		return nil, err
	}

	// Unmarshal to map to sort keys
	var m map[string]interface{}
	if err := json.Unmarshal(jsonBytes, &m); err != nil {
		// If not a map, return original
		return jsonBytes, nil
	}

	// Get sorted keys
	keys := make([]string, 0, len(m))
	for k := range m {
		keys = append(keys, k)
	}
	sort.Strings(keys)

	// Build sorted JSON manually
	var buf bytes.Buffer
	buf.WriteByte('{')
	for i, k := range keys {
		if i > 0 {
			buf.WriteByte(',')
		}
		keyJSON, _ := json.Marshal(k)
		valJSON, _ := json.Marshal(m[k])
		buf.Write(keyJSON)
		buf.WriteByte(':')
		buf.Write(valJSON)
	}
	buf.WriteByte('}')

	return buf.Bytes(), nil
}

// makeRequest makes an authenticated POST request
func (c *Client) makeRequest(endpoint string, data interface{}) (*BaseResponse, error) {
	body, err := sortedJSON(data)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	signature := c.createSignature(body)

	req, err := http.NewRequest("POST", c.config.BaseURL+endpoint, bytes.NewReader(body))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("X-API-KEY", c.config.APIKey)
	req.Header.Set("X-API-SIGN", signature)

	resp, err := c.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response: %w", err)
	}

	var result BaseResponse
	if err := json.Unmarshal(respBody, &result); err != nil {
		return nil, fmt.Errorf("failed to parse response: %w", err)
	}

	return &result, nil
}

// makeGetRequest makes an unauthenticated GET request
func (c *Client) makeGetRequest(endpoint string, result interface{}) error {
	resp, err := c.httpClient.Get(c.config.BaseURL + endpoint)
	if err != nil {
		return fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return fmt.Errorf("failed to read response: %w", err)
	}

	if err := json.Unmarshal(body, result); err != nil {
		return fmt.Errorf("failed to parse response: %w", err)
	}

	return nil
}

// HealthCheck checks API health
func (c *Client) HealthCheck() (*HealthResponse, error) {
	var result HealthResponse
	err := c.makeGetRequest("/health", &result)
	return &result, err
}

// GetCurrencies returns list of supported currencies
func (c *Client) GetCurrencies() (*BaseResponse, error) {
	return c.makeRequest("/api/v2/ccies", map[string]interface{}{})
}

// GetExchangeRate calculates exchange rate
func (c *Client) GetExchangeRate(req PriceRequest) (*BaseResponse, error) {
	return c.makeRequest("/api/v2/price", req)
}

// CreateOrder creates a new exchange order
func (c *Client) CreateOrder(req CreateOrderRequest) (*BaseResponse, error) {
	return c.makeRequest("/api/v2/create", req)
}

// GetOrderStatus gets order status
func (c *Client) GetOrderStatus(req OrderRequest) (*BaseResponse, error) {
	return c.makeRequest("/api/v2/order", req)
}

// SetEmailNotification subscribes to email notifications
func (c *Client) SetEmailNotification(id, token, email string) (*BaseResponse, error) {
	return c.makeRequest("/api/v2/setEmail", map[string]string{
		"id":    id,
		"token": token,
		"email": email,
	})
}

// GetQRCode gets QR code for deposit address
func (c *Client) GetQRCode(id, token string) (*BaseResponse, error) {
	return c.makeRequest("/api/v2/qr", map[string]string{
		"id":    id,
		"token": token,
	})
}

func main() {
	fmt.Println("=== Crypto Exchange API - Go Client ===")
	fmt.Println()

	client := NewClientFromEnv()

	// 1. Health Check
	fmt.Println("1. Health Check:")
	health, err := client.HealthCheck()
	if err != nil {
		fmt.Printf("Error: %v\n", err)
	} else {
		fmt.Printf("Status: %s, Version: %s\n", health.Status, health.Version)
	}
	fmt.Println()

	// 2. Get Currencies
	fmt.Println("2. Get Currencies:")
	currencies, err := client.GetCurrencies()
	if err != nil {
		fmt.Printf("Error: %v\n", err)
	} else if currencies.Code == 0 {
		var currList []Currency
		if err := json.Unmarshal(currencies.Data, &currList); err == nil {
			fmt.Printf("Found %d currencies\n", len(currList))
			if len(currList) > 5 {
				currList = currList[:5]
			}
			for _, c := range currList {
				fmt.Printf("  - %s: %s\n", c.Code, c.Name)
			}
		}
	} else {
		fmt.Printf("API Error: %s\n", currencies.Msg)
	}
	fmt.Println()

	// 3. Get Exchange Rate
	fmt.Println("3. Get Exchange Rate (BTC -> ETH):")
	rate, err := client.GetExchangeRate(PriceRequest{
		FromCcy:   "BTC",
		ToCcy:     "ETH",
		Amount:    0.1,
		Direction: "from",
		Type:      "fixed",
	})
	if err != nil {
		fmt.Printf("Error: %v\n", err)
	} else {
		prettyJSON, _ := json.MarshalIndent(rate, "", "  ")
		fmt.Println(string(prettyJSON))
	}
	fmt.Println()

	fmt.Println("=== Done ===")
}
