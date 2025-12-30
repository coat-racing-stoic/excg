import { apiRequest, publicRequest } from './client';
import type { 
  ExchangeRate, 
  PriceRequest, 
  RateInfo, 
  CachedRateResponse,
  PreviewRate,
  ApiResponse
} from '../types';

/**
 * Получение точного курса через аутентифицированный API
 * Используется на втором экране (подтверждение обмена)
 */
export async function getExchangeRate(params: PriceRequest): Promise<ExchangeRate> {
  const response = await apiRequest<{ exchange_rate: ExchangeRate }>('/api/v2/price', params);
  return response.data.exchange_rate;
}

/**
 * Получение кэшированного курса для пары валют (без аутентификации)
 * Используется для предварительного расчёта на первом экране
 */
export async function getCachedRateForPair(
  from: string, 
  to: string, 
  rateType: 'fixed' | 'float' = 'fixed'
): Promise<CachedRateResponse> {
  const response = await publicRequest<ApiResponse<CachedRateResponse>>(
    `/api/rates/pair/${from}/${to}?rate_type=${rateType}`
  );
  // Handle both wrapped and unwrapped response formats
  if ('rate' in response) {
    return response as unknown as CachedRateResponse;
  }
  return (response as any).data;
}

/**
 * Предварительный расчёт курса из кэша
 * Быстрый расчёт для отображения на первом экране
 */
export async function calculatePreviewRate(
  fromCurrency: string,
  toCurrency: string,
  amount: number,
  rateType: 'fixed' | 'float' = 'fixed'
): Promise<PreviewRate> {
  try {
    const cached = await getCachedRateForPair(fromCurrency, toCurrency, rateType);
    const rate = cached.rate;
    
    // Расчёт получаемой суммы: amount * (out/in)
    const exchangeRate = rate.out / rate.in;
    const toAmount = amount * exchangeRate;
    
    return {
      fromCurrency: rate.from,
      toCurrency: rate.to,
      fromAmount: String(amount),
      toAmount: toAmount.toFixed(8),
      rate: exchangeRate,
      minAmount: rate.minamount,
      maxAmount: rate.maxamount,
      fee: rate.tofee,
      source: cached.source,
    };
  } catch (error) {
    // Fallback: возвращаем демо-данные при ошибке
    console.warn('Failed to get cached rate, using fallback:', error);
    return getFallbackPreviewRate(fromCurrency, toCurrency, amount);
  }
}

/**
 * Fallback расчёт при недоступности кэша
 */
function getFallbackPreviewRate(
  fromCurrency: string,
  toCurrency: string,
  amount: number
): PreviewRate {
  // Примерные курсы для демо
  const demoRates: Record<string, number> = {
    'BTC-ETH': 29.0,
    'ETH-BTC': 0.034,
    'BTC-USDT': 94000,
    'USDT-BTC': 0.0000106,
    'ETH-USDT': 3400,
    'USDT-ETH': 0.00029,
  };
  
  const key = `${fromCurrency}-${toCurrency}`;
  const reverseKey = `${toCurrency}-${fromCurrency}`;
  const rate = demoRates[key] || (demoRates[reverseKey] ? 1 / demoRates[reverseKey] : 1);
  
  return {
    fromCurrency,
    toCurrency,
    fromAmount: String(amount),
    toAmount: (amount * rate * 0.98).toFixed(8), // ~2% fee
    rate,
    minAmount: '0.0001',
    maxAmount: '10',
    fee: 'Included',
    source: 'cache',
  };
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
