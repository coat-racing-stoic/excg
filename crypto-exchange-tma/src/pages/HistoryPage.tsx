import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Layout, Loader } from '../components';
import './HistoryPage.css';

interface StoredOrder {
  id: string;
  token: string;
  createdAt: number;
}

export function HistoryPage() {
  const navigate = useNavigate();
  const [orders, setOrders] = useState<StoredOrder[]>([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    // Load orders from localStorage
    const storedOrders = JSON.parse(localStorage.getItem('orders') || '[]');
    setOrders(storedOrders);
    setLoading(false);
  }, []);
  
  const handleOrderClick = (order: StoredOrder) => {
    navigate(`/order/${order.id}?token=${order.token}`);
  };
  
  const formatDate = (timestamp: number) => {
    return new Date(timestamp).toLocaleString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };
  
  if (loading) {
    return (
      <Layout title="История">
        <div className="history-loading">
          <Loader text="Загрузка истории..." />
        </div>
      </Layout>
    );
  }
  
  return (
    <Layout title="История" subtitle="Ваши последние обмены">
      <div className="history-page">
        {orders.length === 0 ? (
          <div className="history-empty">
            <span className="history-empty-icon">📋</span>
            <h3>История пуста</h3>
            <p>Здесь будут отображаться ваши обмены</p>
          </div>
        ) : (
          <div className="history-list">
            {orders.map((order) => (
              <button
                key={order.id}
                className="history-item"
                onClick={() => handleOrderClick(order)}
              >
                <div className="history-item-info">
                  <span className="history-item-id">#{order.id.slice(0, 12)}...</span>
                  <span className="history-item-date">{formatDate(order.createdAt)}</span>
                </div>
                <span className="history-item-arrow">›</span>
              </button>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
}
