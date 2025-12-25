import { apiRequest, publicRequest } from './client';
import type { Currency } from '../types';

// Backend currency format
interface BackendCurrency {
  code: string;
  coin: string;
  network: string;
  name: string;
  recv: boolean;
  send: boolean;
  tag?: string;
  logo: string;
  color: string;
  priority: number;
}

// Transform backend currency to frontend format
function transformCurrency(bc: BackendCurrency): Currency {
  return {
    code: bc.code,
    name: bc.name,
    network: bc.network,
    icon: bc.logo || getDefaultIcon(bc.code),
    send: bc.send,
    recv: bc.recv,
    tag: bc.tag,
    priority: bc.priority,
  };
}

function getDefaultIcon(code: string): string {
  const icons: Record<string, string> = {
    BTC: '₿',
    ETH: 'Ξ',
    USDT: '₮',
    USDC: '$',
    BNB: 'B',
    SOL: '◎',
    XRP: '✕',
    DOGE: 'Ð',
    LTC: 'Ł',
    TRX: 'T',
    ADA: '₳',
    DOT: '●',
    MATIC: 'M',
    AVAX: 'A',
    LINK: '⬡',
  };
  return icons[code] || code.charAt(0);
}

export async function getCurrencies(): Promise<Currency[]> {
  try {
    const response = await apiRequest<BackendCurrency[]>('/api/v2/ccies');
    if (Array.isArray(response.data)) {
      return response.data.map(transformCurrency);
    }
    return [];
  } catch (error) {
    console.error('Failed to get currencies:', error);
    throw error;
  }
}

interface AvailableCurrenciesResponse {
  direction: string;
  count: number;
  currencies: string[];
}

export async function getAvailableCurrencies(
  direction: 'both' | 'send' | 'receive' = 'both'
): Promise<Currency[]> {
  try {
    // First try to get full currency list from authenticated endpoint
    const currencies = await getCurrencies();
    
    // Filter by direction
    if (direction === 'send') {
      return currencies.filter(c => c.send);
    } else if (direction === 'receive') {
      return currencies.filter(c => c.recv);
    }
    return currencies;
  } catch {
    // Fallback to public endpoint which returns only codes
    try {
      const response = await publicRequest<AvailableCurrenciesResponse>(
        `/api/currencies/available?direction=${direction}`
      );
      
      // Convert codes to basic Currency objects
      return response.currencies.map(code => ({
        code,
        name: code,
        network: code,
        icon: getDefaultIcon(code),
        send: direction !== 'receive',
        recv: direction !== 'send',
      }));
    } catch (error) {
      console.error('Failed to get available currencies:', error);
      throw error;
    }
  }
}

interface ValidateCurrencyResponse {
  valid: boolean;
  currency?: BackendCurrency;
}

export async function validateCurrency(code: string): Promise<{ valid: boolean; currency?: Currency }> {
  try {
    const response = await publicRequest<ValidateCurrencyResponse>(`/api/currencies/validate/${code}`);
    return {
      valid: response.valid,
      currency: response.currency ? transformCurrency(response.currency) : undefined,
    };
  } catch (error) {
    console.error('Failed to validate currency:', error);
    return { valid: false };
  }
}
