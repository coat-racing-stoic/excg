import CryptoJS from 'crypto-js';
import type { ApiResponse } from '../types';

// API configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';
const API_KEY = import.meta.env.VITE_API_KEY || 'demo_api_key';
const API_SECRET = import.meta.env.VITE_API_SECRET || 'demo_api_secret';

// Retry configuration
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000;

function createSignature(data: object): string {
  // Use the same JSON format as will be sent in the request body
  const jsonStr = JSON.stringify(data);
  return CryptoJS.HmacSHA256(jsonStr, API_SECRET).toString();
}

async function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

export async function apiRequest<T>(
  endpoint: string,
  data: object = {},
  retries = MAX_RETRIES
): Promise<ApiResponse<T>> {
  const signature = createSignature(data);
  const url = endpoint.startsWith('/api') ? endpoint : `${API_BASE_URL}${endpoint}`;
  
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-KEY': API_KEY,
        'X-API-SIGN': signature,
      },
      body: JSON.stringify(data),
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      
      // Retry on server errors
      if (response.status >= 500 && retries > 0) {
        console.warn(`API request failed (${response.status}), retrying...`);
        await delay(RETRY_DELAY);
        return apiRequest<T>(endpoint, data, retries - 1);
      }
      
      throw new Error(`API Error: ${response.status} - ${errorText}`);
    }
    
    const result = await response.json();
    
    // Check for API-level errors
    if (result.code !== 0) {
      throw new Error(result.msg || 'Unknown API error');
    }
    
    return result;
  } catch (error) {
    // Retry on network errors
    if (retries > 0 && error instanceof TypeError) {
      console.warn('Network error, retrying...', error);
      await delay(RETRY_DELAY);
      return apiRequest<T>(endpoint, data, retries - 1);
    }
    throw error;
  }
}

export async function publicRequest<T>(
  endpoint: string,
  retries = MAX_RETRIES
): Promise<T> {
  const url = endpoint.startsWith('/api') ? endpoint : `${API_BASE_URL}${endpoint}`;
  
  try {
    const response = await fetch(url);
    
    if (!response.ok) {
      const errorText = await response.text();
      
      // Retry on server errors
      if (response.status >= 500 && retries > 0) {
        console.warn(`Public request failed (${response.status}), retrying...`);
        await delay(RETRY_DELAY);
        return publicRequest<T>(endpoint, retries - 1);
      }
      
      throw new Error(`API Error: ${response.status} - ${errorText}`);
    }
    
    const result = await response.json();
    
    // Handle wrapped response format
    if (result.code !== undefined) {
      if (result.code !== 0) {
        throw new Error(result.msg || 'Unknown API error');
      }
      return result.data as T;
    }
    
    return result as T;
  } catch (error) {
    // Retry on network errors
    if (retries > 0 && error instanceof TypeError) {
      console.warn('Network error, retrying...', error);
      await delay(RETRY_DELAY);
      return publicRequest<T>(endpoint, retries - 1);
    }
    throw error;
  }
}

export { API_BASE_URL };
