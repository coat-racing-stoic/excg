import { useState } from 'react';
import { OrderStatus } from './OrderStatus';
import { Button } from '../common';
import type { Order } from '../../types';
import './OrderDetails.css';

interface OrderDetailsProps {
  order: Order;
  onCopyAddress?: () => void;
}

export function OrderDetails({ order, onCopyAddress }: OrderDetailsProps) {
  const [copied, setCopied] = useState(false);
  
  const handleCopy = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      onCopyAddress?.();
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };
  
  const timeLeft = order.time.left ? Math.max(0, order.time.left) : 0;
  const minutes = Math.floor(timeLeft / 60);
  const seconds = timeLeft % 60;
  
  return (
    <div className="order-details">
      <div className="order-details-header">
        <span className="order-id">#{order.id}</span>
        <OrderStatus status={order.status} showDescription={false} />
      </div>
      
      {order.status === 'NEW' && order.from.address && (
        <div className="order-deposit">
          <div className="order-deposit-header">
            <span className="order-deposit-label">Отправьте</span>
            {timeLeft > 0 && (
              <span className="order-timer">
                ⏱️ {minutes}:{seconds.toString().padStart(2, '0')}
              </span>
            )}
          </div>
          
          <div className="order-deposit-amount">
            <span className="order-amount">{order.from.amount}</span>
            <span className="order-currency">{order.from.code}</span>
          </div>
          
          <div className="order-address-container">
            <span className="order-address-label">На адрес:</span>
            <div className="order-address">
              <span className="order-address-text">{order.from.address}</span>
              <Button 
                size="small" 
                variant="outline"
                onClick={() => handleCopy(order.from.address!)}
              >
                {copied ? '✓' : 'Копировать'}
              </Button>
            </div>
          </div>
          
          {order.from.tag && (
            <div className="order-tag">
              <span className="order-tag-label">Memo/Tag:</span>
              <span className="order-tag-value">{order.from.tag}</span>
            </div>
          )}
        </div>
      )}
      
      <div className="order-exchange-info">
        <div className="order-exchange-row">
          <div className="order-exchange-item">
            <span className="order-exchange-label">Отправляете</span>
            <span className="order-exchange-value">
              {order.from.amount} {order.from.code}
            </span>
            <span className="order-exchange-network">{order.from.network}</span>
          </div>
          
          <div className="order-exchange-arrow">→</div>
          
          <div className="order-exchange-item">
            <span className="order-exchange-label">Получаете</span>
            <span className="order-exchange-value">
              {order.to.amount} {order.to.code}
            </span>
            <span className="order-exchange-network">{order.to.network}</span>
          </div>
        </div>
      </div>
      
      <div className="order-recipient">
        <span className="order-recipient-label">Адрес получателя:</span>
        <span className="order-recipient-address">{order.to.address}</span>
      </div>
      
      {order.to.txid && (
        <div className="order-txid">
          <span className="order-txid-label">Transaction ID:</span>
          <span className="order-txid-value">{order.to.txid}</span>
        </div>
      )}
    </div>
  );
}
