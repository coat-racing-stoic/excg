import { useState, useEffect, useCallback } from 'react';
import { getAvailableCurrencies } from '../api';
import type { Currency } from '../types';

interface UseCurrenciesResult {
  currencies: Currency[];
  sendCurrencies: Currency[];
  receiveCurrencies: Currency[];
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export function useCurrencies(): UseCurrenciesResult {
  const [currencies, setCurrencies] = useState<Currency[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const fetchCurrencies = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await getAvailableCurrencies('both');
      setCurrencies(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load currencies');
      // Fallback to demo data
      setCurrencies(getDemoCurrencies());
    } finally {
      setLoading(false);
    }
  }, []);
  
  useEffect(() => {
    fetchCurrencies();
  }, [fetchCurrencies]);
  
  const sendCurrencies = currencies.filter(c => c.send);
  const receiveCurrencies = currencies.filter(c => c.recv);
  
  return {
    currencies,
    sendCurrencies,
    receiveCurrencies,
    loading,
    error,
    refetch: fetchCurrencies,
  };
}

function getDemoCurrencies(): Currency[] {
  return [
    { code: 'BTC', name: 'Bitcoin', network: 'BTC', icon: '₿', send: true, recv: true, min: 0.0001, max: 10 },
    { code: 'ETH', name: 'Ethereum', network: 'ETH', icon: 'Ξ', send: true, recv: true, min: 0.01, max: 100 },
    { code: 'USDT', name: 'Tether', network: 'TRC20', icon: '₮', send: true, recv: true, min: 10, max: 100000 },
    { code: 'USDT', name: 'Tether', network: 'ERC20', icon: '₮', send: true, recv: true, min: 50, max: 100000 },
    { code: 'BNB', name: 'BNB', network: 'BSC', icon: 'B', send: true, recv: true, min: 0.1, max: 500 },
    { code: 'SOL', name: 'Solana', network: 'SOL', icon: 'S', send: true, recv: true, min: 0.5, max: 1000 },
    { code: 'XRP', name: 'Ripple', network: 'XRP', icon: 'X', send: true, recv: true, min: 10, max: 50000 },
    { code: 'DOGE', name: 'Dogecoin', network: 'DOGE', icon: 'Ð', send: true, recv: true, min: 50, max: 100000 },
    { code: 'LTC', name: 'Litecoin', network: 'LTC', icon: 'Ł', send: true, recv: true, min: 0.1, max: 500 },
    { code: 'TRX', name: 'TRON', network: 'TRX', icon: 'T', send: true, recv: true, min: 100, max: 500000 },
  ];
}
