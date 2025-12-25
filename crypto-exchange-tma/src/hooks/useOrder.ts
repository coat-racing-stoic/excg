import { useState, useEffect, useCallback } from 'react';
import { getOrderStatus } from '../api';
import type { Order, OrderStatus } from '../types';

interface UseOrderResult {
  order: Order | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export function useOrder(orderId: string | null, token: string | null): UseOrderResult {
  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const fetchOrder = useCallback(async () => {
    if (!orderId || !token) {
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const data = await getOrderStatus({ id: orderId, token });
      setOrder(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load order');
    } finally {
      setLoading(false);
    }
  }, [orderId, token]);
  
  useEffect(() => {
    fetchOrder();
    
    // Auto-refresh every 10 seconds for active orders
    const interval = setInterval(() => {
      if (order && !isOrderComplete(order.status)) {
        fetchOrder();
      }
    }, 10000);
    
    return () => clearInterval(interval);
  }, [fetchOrder, order?.status]);
  
  return {
    order,
    loading,
    error,
    refetch: fetchOrder,
  };
}

function isOrderComplete(status: OrderStatus): boolean {
  return ['DONE', 'EXPIRED', 'FAILED'].includes(status);
}

export function getStatusInfo(status: OrderStatus): { label: string; color: string; description: string } {
  const statusMap: Record<OrderStatus, { label: string; color: string; description: string }> = {
    NEW: { 
      label: 'Новый', 
      color: '#ffd700', 
      description: 'Ожидание депозита' 
    },
    PENDING: { 
      label: 'Ожидание', 
      color: '#ff9800', 
      description: 'Ожидание подтверждений' 
    },
    EXCHANGE: { 
      label: 'Обмен', 
      color: '#2196f3', 
      description: 'Обмен в процессе' 
    },
    WITHDRAW: { 
      label: 'Отправка', 
      color: '#9c27b0', 
      description: 'Отправка средств' 
    },
    DONE: { 
      label: 'Завершён', 
      color: '#4caf50', 
      description: 'Обмен успешно завершён' 
    },
    EXPIRED: { 
      label: 'Истёк', 
      color: '#f44336', 
      description: 'Время ордера истекло' 
    },
    EMERGENCY: { 
      label: 'Проблема', 
      color: '#ff5722', 
      description: 'Требуется действие' 
    },
    FAILED: { 
      label: 'Ошибка', 
      color: '#f44336', 
      description: 'Обмен не удался' 
    },
  };
  
  return statusMap[status] || { label: status, color: '#999', description: '' };
}
