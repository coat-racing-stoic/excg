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

export interface ExchangeRate {
  from: {
    code: string;
    network: string;
    amount: string;
    min: string;
    max: string;
  };
  to: {
    code: string;
    network: string;
    amount: string;
    rate: string;
  };
  errors?: string[];
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
