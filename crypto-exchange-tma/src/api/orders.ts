import { apiRequest } from './client';
import type { Order, CreateOrderRequest, OrderStatusRequest } from '../types';

export async function createOrder(params: CreateOrderRequest): Promise<Order> {
  const response = await apiRequest<Order>('/api/v2/create', params);
  return response.data;
}

export async function getOrderStatus(params: OrderStatusRequest): Promise<Order> {
  const response = await apiRequest<Order>('/api/v2/order', params);
  return response.data;
}

export async function setOrderEmail(
  orderId: string, 
  token: string, 
  email: string
): Promise<{ success: boolean }> {
  const response = await apiRequest<{ success: boolean }>('/api/v2/setEmail', { 
    id: orderId, 
    token, 
    email 
  });
  return response.data;
}

export async function getOrderQR(
  orderId: string, 
  token: string
): Promise<{ address: string; qr: string }> {
  const response = await apiRequest<{ address: string; qr: string }>('/api/v2/qr', { 
    id: orderId, 
    token 
  });
  return response.data;
}

export async function handleEmergency(
  orderId: string, 
  token: string, 
  choice: string, 
  address?: string
): Promise<{ success: boolean; message: string }> {
  const response = await apiRequest<{ success: boolean; message: string }>('/api/v2/emergency', { 
    id: orderId, 
    token, 
    choice, 
    address 
  });
  return response.data;
}
