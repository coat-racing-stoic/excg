import { useState, useCallback } from 'react';
import { getExchangeRate, createOrder } from '../api';
import type { Currency, ExchangeRate, Order, PriceRequest, CreateOrderRequest } from '../types';

interface UseExchangeResult {
  fromCurrency: Currency | null;
  toCurrency: Currency | null;
  amount: string;
  toAddress: string;
  exchangeType: 'fixed' | 'float';
  rate: ExchangeRate | null;
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
  const [rate, setRate] = useState<ExchangeRate | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const swapCurrencies = useCallback(() => {
    const temp = fromCurrency;
    setFromCurrency(toCurrency);
    setToCurrency(temp);
    setRate(null);
  }, [fromCurrency, toCurrency]);
  
  const calculateRate = useCallback(async () => {
    if (!fromCurrency || !toCurrency || !amount || parseFloat(amount) <= 0) {
      setRate(null);
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const params: PriceRequest = {
        type: exchangeType,
        fromCcy: `${fromCurrency.code}${fromCurrency.network}`,
        toCcy: `${toCurrency.code}${toCurrency.network}`,
        direction: 'from',
        amount: parseFloat(amount),
      };
      
      const rateData = await getExchangeRate(params);
      setRate(rateData);
      
      if (rateData.errors && rateData.errors.length > 0) {
        setError(rateData.errors.join(', '));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to calculate rate');
      // Demo rate calculation
      setRate(getDemoRate(fromCurrency, toCurrency, amount));
    } finally {
      setLoading(false);
    }
  }, [fromCurrency, toCurrency, amount, exchangeType]);
  
  const submitOrder = useCallback(async (): Promise<Order | null> => {
    if (!fromCurrency || !toCurrency || !amount || !toAddress) {
      setError('Please fill all required fields');
      return null;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const params: CreateOrderRequest = {
        type: exchangeType,
        fromCcy: `${fromCurrency.code}${fromCurrency.network}`,
        toCcy: `${toCurrency.code}${toCurrency.network}`,
        direction: 'from',
        amount: parseFloat(amount),
        toAddress,
      };
      
      const order = await createOrder(params);
      return order;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create order');
      // Return demo order for testing
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
    setRate(null);
    setError(null);
  }, []);
  
  return {
    fromCurrency,
    toCurrency,
    amount,
    toAddress,
    exchangeType,
    rate,
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

function getDemoRate(from: Currency, to: Currency, amount: string): ExchangeRate {
  const rates: Record<string, number> = {
    'BTC-ETH': 15.5,
    'ETH-BTC': 0.064,
    'BTC-USDT': 43000,
    'USDT-BTC': 0.000023,
    'ETH-USDT': 2600,
    'USDT-ETH': 0.00038,
  };
  
  const key = `${from.code}-${to.code}`;
  const reverseKey = `${to.code}-${from.code}`;
  const rateValue = rates[key] || (rates[reverseKey] ? 1 / rates[reverseKey] : 1);
  
  const amountNum = parseFloat(amount);
  const toAmount = (amountNum * rateValue * 0.98).toFixed(8); // 2% fee
  
  return {
    from: {
      code: from.code,
      network: from.network,
      amount: amount,
      min: String(from.min || 0.001),
      max: String(from.max || 10),
    },
    to: {
      code: to.code,
      network: to.network,
      amount: toAmount,
      rate: String(rateValue),
    },
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
      address: '1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa', // Demo address
    },
    to: {
      code: to.code,
      network: to.network,
      amount: (parseFloat(amount) * 15).toFixed(8),
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
