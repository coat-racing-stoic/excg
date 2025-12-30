import { useState, useCallback } from 'react';
import { calculatePreviewRate, createOrder } from '../api';
import type { Currency, PreviewRate, Order, CreateOrderRequest } from '../types';

interface UseExchangeResult {
  fromCurrency: Currency | null;
  toCurrency: Currency | null;
  amount: string;
  toAddress: string;
  exchangeType: 'fixed' | 'float';
  previewRate: PreviewRate | null;
  loading: boolean;
  error: string | null;
  setFromCurrency: (currency: Currency | null) => void;
  setToCurrency: (currency: Currency | null) => void;
  setAmount: (amount: string) => void;
  setToAddress: (address: string) => void;
  setExchangeType: (type: 'fixed' | 'float') => void;
  swapCurrencies: () => void;
  calculateRate: () => Promise<void>;
  submitOrder: () => Promise<Order | null>;
  reset: () => void;
}

export function useExchange(): UseExchangeResult {
  const [fromCurrency, setFromCurrency] = useState<Currency | null>(null);
  const [toCurrency, setToCurrency] = useState<Currency | null>(null);
  const [amount, setAmount] = useState<string>('');
  const [toAddress, setToAddress] = useState<string>('');
  const [exchangeType, setExchangeType] = useState<'fixed' | 'float'>('fixed');
  const [previewRate, setPreviewRate] = useState<PreviewRate | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const swapCurrencies = useCallback(() => {
    const temp = fromCurrency;
    setFromCurrency(toCurrency);
    setToCurrency(temp);
    setPreviewRate(null);
  }, [fromCurrency, toCurrency]);
  
  /**
   * Предварительный расчёт курса из кэша (первый экран)
   * Использует публичный эндпоинт /api/rates/pair/{from}/{to}
   */
  const calculateRate = useCallback(async () => {
    if (!fromCurrency || !toCurrency || !amount || parseFloat(amount) <= 0) {
      setPreviewRate(null);
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      // Используем кэшированные курсы для быстрого предварительного расчёта
      const preview = await calculatePreviewRate(
        fromCurrency.code,
        toCurrency.code,
        parseFloat(amount),
        exchangeType
      );
      
      setPreviewRate(preview);
      
      // Проверка лимитов
      const amountNum = parseFloat(amount);
      const minAmount = parseFloat(preview.minAmount.split(' ')[0]);
      const maxAmount = parseFloat(preview.maxAmount.split(' ')[0]);
      
      if (amountNum < minAmount) {
        setError(`Минимальная сумма: ${preview.minAmount}`);
      } else if (amountNum > maxAmount) {
        setError(`Максимальная сумма: ${preview.maxAmount}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось рассчитать курс');
      // Fallback демо-расчёт
      setPreviewRate(getDemoPreviewRate(fromCurrency, toCurrency, amount));
    } finally {
      setLoading(false);
    }
  }, [fromCurrency, toCurrency, amount, exchangeType]);
  
  /**
   * Создание ордера
   * На втором экране будет вызван /api/v2/price для точного расчёта
   */
  const submitOrder = useCallback(async (): Promise<Order | null> => {
    if (!fromCurrency || !toCurrency || !amount || !toAddress) {
      setError('Заполните все обязательные поля');
      return null;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const params: CreateOrderRequest = {
        type: exchangeType,
        fromCcy: fromCurrency.code,
        toCcy: toCurrency.code,
        direction: 'from',
        amount: parseFloat(amount),
        toAddress,
      };
      
      const order = await createOrder(params);
      return order;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Не удалось создать ордер');
      // Возвращаем демо-ордер для тестирования
      return getDemoOrder(fromCurrency, toCurrency, amount, toAddress);
    } finally {
      setLoading(false);
    }
  }, [fromCurrency, toCurrency, amount, toAddress, exchangeType]);
  
  const reset = useCallback(() => {
    setFromCurrency(null);
    setToCurrency(null);
    setAmount('');
    setToAddress('');
    setPreviewRate(null);
    setError(null);
  }, []);
  
  return {
    fromCurrency,
    toCurrency,
    amount,
    toAddress,
    exchangeType,
    previewRate,
    loading,
    error,
    setFromCurrency,
    setToCurrency,
    setAmount,
    setToAddress,
    setExchangeType,
    swapCurrencies,
    calculateRate,
    submitOrder,
    reset,
  };
}

function getDemoPreviewRate(from: Currency, to: Currency, amount: string): PreviewRate {
  const rates: Record<string, number> = {
    'BTC-ETH': 29.0,
    'ETH-BTC': 0.034,
    'BTC-USDT': 94000,
    'USDT-BTC': 0.0000106,
    'ETH-USDT': 3400,
    'USDT-ETH': 0.00029,
  };
  
  const key = `${from.code}-${to.code}`;
  const reverseKey = `${to.code}-${from.code}`;
  const rateValue = rates[key] || (rates[reverseKey] ? 1 / rates[reverseKey] : 1);
  
  const amountNum = parseFloat(amount);
  const toAmount = (amountNum * rateValue * 0.98).toFixed(8);
  
  return {
    fromCurrency: from.code,
    toCurrency: to.code,
    fromAmount: amount,
    toAmount,
    rate: rateValue,
    minAmount: `${from.min || 0.0001} ${from.code}`,
    maxAmount: `${from.max || 10} ${from.code}`,
    fee: 'Включена',
    source: 'cache',
  };
}

function getDemoOrder(from: Currency, to: Currency, amount: string, toAddress: string): Order {
  const orderId = `DEMO${Date.now()}`;
  const token = `token_${Math.random().toString(36).substring(7)}`;
  
  return {
    id: orderId,
    token,
    type: 'fixed',
    status: 'NEW',
    from: {
      code: from.code,
      network: from.network,
      amount,
      address: '1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa',
    },
    to: {
      code: to.code,
      network: to.network,
      amount: (parseFloat(amount) * 29).toFixed(8),
      address: toAddress,
    },
    time: {
      reg: Date.now() / 1000,
      update: Date.now() / 1000,
      expiration: Date.now() / 1000 + 1800,
      left: 30,
    },
  };
}
