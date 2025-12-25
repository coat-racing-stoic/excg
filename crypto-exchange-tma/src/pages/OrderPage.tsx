import { useEffect, useState } from 'react';
import { useParams, useSearchParams, useNavigate } from 'react-router-dom';
import { Layout, Loader, Button } from '../components';
import { OrderDetails } from '../components/order';
import { useOrder, useTelegram } from '../hooks';
import './OrderPage.css';

export function OrderPage() {
  const { orderId } = useParams<{ orderId: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get('token');
  
  const { 
    showBackButton, 
    hideBackButton, 
    onBackButtonClick,
    notificationVibrate,
    vibrate,
  } = useTelegram();
  
  const { order, loading, error, refetch } = useOrder(orderId || null, token);
  const [prevStatus, setPrevStatus] = useState<string | null>(null);
  
  // Setup back button
  useEffect(() => {
    showBackButton();
    const cleanup = onBackButtonClick(() => navigate('/'));
    
    return () => {
      hideBackButton();
      cleanup();
    };
  }, [showBackButton, hideBackButton, onBackButtonClick, navigate]);
  
  // Notify on status change
  useEffect(() => {
    if (order && prevStatus && order.status !== prevStatus) {
      if (order.status === 'DONE') {
        notificationVibrate('success');
      } else if (order.status === 'FAILED' || order.status === 'EXPIRED') {
        notificationVibrate('error');
      } else {
        vibrate('light');
      }
    }
    if (order) {
      setPrevStatus(order.status);
    }
  }, [order?.status]);
  
  const handleCopyAddress = () => {
    vibrate('light');
  };
  
  if (loading && !order) {
    return (
      <Layout title="Загрузка..." showNavigation={false}>
        <div className="order-page-loading">
          <Loader size="large" text="Загрузка ордера..." />
        </div>
      </Layout>
    );
  }
  
  if (error && !order) {
    return (
      <Layout title="Ошибка" showNavigation={false}>
        <div className="order-page-error">
          <span className="error-icon">❌</span>
          <h2>Ордер не найден</h2>
          <p>{error}</p>
          <Button onClick={() => navigate('/')}>
            Вернуться на главную
          </Button>
        </div>
      </Layout>
    );
  }
  
  if (!order) {
    return null;
  }
  
  return (
    <Layout 
      title={`Ордер #${order.id.slice(0, 8)}...`} 
      subtitle={getStatusSubtitle(order.status)}
      showNavigation={false}
    >
      <div className="order-page">
        <OrderDetails order={order} onCopyAddress={handleCopyAddress} />
        
        <div className="order-actions">
          {order.status === 'DONE' && (
            <Button fullWidth onClick={() => navigate('/')}>
              Новый обмен
            </Button>
          )}
          
          {(order.status === 'NEW' || order.status === 'PENDING') && (
            <Button 
              fullWidth 
              variant="outline" 
              onClick={refetch}
              loading={loading}
            >
              Обновить статус
            </Button>
          )}
        </div>
      </div>
    </Layout>
  );
}

function getStatusSubtitle(status: string): string {
  const subtitles: Record<string, string> = {
    NEW: 'Ожидание депозита',
    PENDING: 'Подтверждение транзакции',
    EXCHANGE: 'Обмен в процессе',
    WITHDRAW: 'Отправка средств',
    DONE: 'Обмен завершён',
    EXPIRED: 'Время истекло',
    EMERGENCY: 'Требуется действие',
    FAILED: 'Ошибка обмена',
  };
  return subtitles[status] || '';
}
