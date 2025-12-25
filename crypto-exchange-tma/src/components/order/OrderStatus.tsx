
import { getStatusInfo } from '../../hooks/useOrder';
import type { OrderStatus as OrderStatusType } from '../../types';
import './OrderStatus.css';

interface OrderStatusProps {
  status: OrderStatusType;
  showDescription?: boolean;
}

export function OrderStatus({ status, showDescription = true }: OrderStatusProps) {
  const { label, color, description } = getStatusInfo(status);
  
  return (
    <div className="order-status">
      <div className="order-status-badge" style={{ backgroundColor: color }}>
        <span className="order-status-dot" />
        <span className="order-status-label">{label}</span>
      </div>
      {showDescription && description && (
        <p className="order-status-description">{description}</p>
      )}
    </div>
  );
}
