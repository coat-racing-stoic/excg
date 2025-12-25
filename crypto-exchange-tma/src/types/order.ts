export type OrderStatus = 
  | 'NEW' 
  | 'PENDING' 
  | 'EXCHANGE' 
  | 'WITHDRAW' 
  | 'DONE' 
  | 'EXPIRED' 
  | 'EMERGENCY' 
  | 'FAILED';

export interface OrderCurrency {
  code: string;
  network: string;
  amount: string;
  address?: string;
  tag?: string;
  txid?: string;
  confirmations?: number;
}

export interface OrderTime {
  reg: number;
  start?: number;
  finish?: number;
  update: number;
  expiration: number;
  left: number;
}

export interface Order {
  id: string;
  token: string;
  type: 'fixed' | 'float';
  status: OrderStatus;
  from: OrderCurrency;
  to: OrderCurrency;
  time: OrderTime;
  emergency?: {
    status: string[];
    choice?: string;
    repeat?: string;
  };
}

export interface CreateOrderRequest {
  type: 'fixed' | 'float';
  fromCcy: string;
  toCcy: string;
  direction: 'from' | 'to';
  amount: number;
  toAddress: string;
  toTag?: string;
  refcode?: string;
  afftax?: number;
}

export interface OrderStatusRequest {
  id: string;
  token: string;
}
