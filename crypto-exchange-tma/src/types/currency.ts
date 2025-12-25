export interface Currency {
  code: string;
  name: string;
  network: string;
  icon: string;
  send: boolean;
  recv: boolean;
  tag?: string;
  priority?: number;
  min?: number;
  max?: number;
}

export interface CurrencyPair {
  from: Currency;
  to: Currency;
}
