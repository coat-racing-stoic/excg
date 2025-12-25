import { apiRequest, publicRequest } from './client';
import type { Currency } from '../types';

export async function getCurrencies(): Promise<Currency[]> {
  const response = await apiRequest<Currency[]>('/api/v2/ccies');
  return response.data;
}

export async function getAvailableCurrencies(
  direction: 'both' | 'send' | 'receive' = 'both'
): Promise<Currency[]> {
  return publicRequest<Currency[]>(`/api/currencies/available?direction=${direction}`);
}

export async function validateCurrency(code: string): Promise<{ valid: boolean; currency?: Currency }> {
  return publicRequest(`/api/currencies/validate/${code}`);
}
