import CryptoJS from 'crypto-js';
import type { ApiResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:12000';
const API_KEY = import.meta.env.VITE_API_KEY || '';
const API_SECRET = import.meta.env.VITE_API_SECRET || '';

function createSignature(data: object): string {
  const jsonStr = JSON.stringify(data, Object.keys(data).sort());
  return CryptoJS.HmacSHA256(jsonStr, API_SECRET).toString();
}

export async function apiRequest<T>(
  endpoint: string,
  data: object = {}
): Promise<ApiResponse<T>> {
  const signature = createSignature(data);
  
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
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
    throw new Error(`API Error: ${response.status} - ${errorText}`);
  }
  
  return response.json();
}

export async function publicRequest<T>(endpoint: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`);
  
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`API Error: ${response.status} - ${errorText}`);
  }
  
  return response.json();
}

export { API_BASE_URL };
