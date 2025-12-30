export interface ApiResponse<T> {
  code: number;
  msg: string;
  data: T;
}

export interface PriceRequest {
  type: 'fixed' | 'float';
  fromCcy: string;
  toCcy: string;
  direction: 'from' | 'to';
  amount: number;
  refcode?: string;
  afftax?: number;
}

// Ответ от /api/v2/price (точный расчёт)
export interface ExchangeRate {
  from: {
    code: string;
    network: string;
    coin: string;
    amount: string;
    rate: string;
    precision: number;
    min: string;
    max: string;
    usd: string;
    btc?: string;
  };
  to: {
    code: string;
    network: string;
    coin: string;
    amount: string;
    rate: string;
    precision: number;
    min: string;
    max: string;
    usd: string;
    btc?: string;
  };
  errors?: string[];
}

// Кэшированный курс из /api/rates/pair/{from}/{to}
export interface CachedRate {
  from: string;
  to: string;
  in: number;
  out: number;
  amount: number;
  tofee: string;
  minamount: string;
  maxamount: string;
}

export interface CachedRateResponse {
  rate: CachedRate;
  source: 'cache' | 'api';
}

// Предварительный расчёт для первого экрана
export interface PreviewRate {
  fromCurrency: string;
  toCurrency: string;
  fromAmount: string;
  toAmount: string;
  rate: number;
  minAmount: string;
  maxAmount: string;
  fee: string;
  source: 'cache' | 'api';
}

export interface RateInfo {
  from: string;
  to: string;
  in: string;
  out: string;
  amount: string;
  minamount: string;
  maxamount: string;
}
