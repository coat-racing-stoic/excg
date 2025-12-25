import { apiRequest, publicRequest } from './client';
import type { ExchangeRate, PriceRequest, RateInfo } from '../types';

export async function getExchangeRate(params: PriceRequest): Promise<ExchangeRate> {
  const response = await apiRequest<{ exchange_rate: ExchangeRate }>('/api/v2/price', params);
  return response.data.exchange_rate;
}

export async function getFixedRates(): Promise<RateInfo[]> {
  return publicRequest<RateInfo[]>('/api/rates/fixed');
}

export async function getFloatRates(): Promise<RateInfo[]> {
  return publicRequest<RateInfo[]>('/api/rates/float');
}

export async function getRateForPair(from: string, to: string): Promise<RateInfo> {
  return publicRequest<RateInfo>(`/api/rates/pair/${from}/${to}`);
}
