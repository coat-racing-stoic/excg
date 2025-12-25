import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Layout, Button, Input } from '../components';
import { 
  CurrencySelector, 
  AmountInput, 
  ExchangeRate, 
  ExchangeTypeToggle 
} from '../components/exchange';
import { useCurrencies, useExchange, useTelegram } from '../hooks';
import './HomePage.css';

export function HomePage() {
  const navigate = useNavigate();
  const { vibrate, notificationVibrate, setMainButton, hideMainButton } = useTelegram();
  const { sendCurrencies, receiveCurrencies, loading: currenciesLoading } = useCurrencies();
  const {
    fromCurrency,
    toCurrency,
    amount,
    toAddress,
    exchangeType,
    rate,
    loading,
    error,
    setFromCurrency,
    setToCurrency,
    setAmount,
    setToAddress,
    setExchangeType,
    swapCurrencies,
    calculateRate,
    submitOrder,
  } = useExchange();
  
  // Calculate rate when inputs change
  useEffect(() => {
    const timer = setTimeout(() => {
      if (fromCurrency && toCurrency && amount) {
        calculateRate();
      }
    }, 500);
    
    return () => clearTimeout(timer);
  }, [fromCurrency, toCurrency, amount, exchangeType, calculateRate]);
  
  // Setup main button
  useEffect(() => {
    const canSubmit = fromCurrency && toCurrency && amount && toAddress && rate && !loading;
    
    if (canSubmit) {
      const cleanup = setMainButton('Создать обмен', handleSubmit, {
        isEnabled: true,
        isLoading: loading,
      });
      return cleanup;
    } else {
      hideMainButton();
    }
  }, [fromCurrency, toCurrency, amount, toAddress, rate, loading]);
  
  const handleSwap = () => {
    vibrate('light');
    swapCurrencies();
  };
  
  const handleSubmit = async () => {
    vibrate('medium');
    const order = await submitOrder();
    
    if (order) {
      notificationVibrate('success');
      // Store order in localStorage for demo
      const orders = JSON.parse(localStorage.getItem('orders') || '[]');
      orders.unshift({ id: order.id, token: order.token, createdAt: Date.now() });
      localStorage.setItem('orders', JSON.stringify(orders.slice(0, 10)));
      
      navigate(`/order/${order.id}?token=${order.token}`);
    } else {
      notificationVibrate('error');
    }
  };
  
  return (
    <Layout title="Crypto Exchange" subtitle="Быстрый и безопасный обмен">
      <div className="home-page">
        <ExchangeTypeToggle 
          value={exchangeType} 
          onChange={setExchangeType} 
        />
        
        <div className="exchange-form">
          <CurrencySelector
            label="Отправляете"
            currencies={sendCurrencies}
            selected={fromCurrency}
            onSelect={setFromCurrency}
            disabled={currenciesLoading}
          />
          
          <AmountInput
            value={amount}
            onChange={setAmount}
            currency={fromCurrency}
            label="Сумма"
            disabled={!fromCurrency}
          />
          
          <button className="swap-button" onClick={handleSwap}>
            <span className="swap-icon">⇅</span>
          </button>
          
          <CurrencySelector
            label="Получаете"
            currencies={receiveCurrencies}
            selected={toCurrency}
            onSelect={setToCurrency}
            disabled={currenciesLoading}
          />
          
          <ExchangeRate
            rate={rate}
            fromCurrency={fromCurrency}
            toCurrency={toCurrency}
            isLoading={loading && !!amount}
          />
          
          <Input
            value={toAddress}
            onChange={setToAddress}
            label={`Адрес ${toCurrency?.code || ''} кошелька`}
            placeholder="Введите адрес получателя"
            disabled={!toCurrency}
          />
          
          {error && (
            <div className="error-message">
              ⚠️ {error}
            </div>
          )}
        </div>
        
        <Button
          fullWidth
          size="large"
          onClick={handleSubmit}
          disabled={!fromCurrency || !toCurrency || !amount || !toAddress || !rate || loading}
          loading={loading}
        >
          Создать обмен
        </Button>
      </div>
    </Layout>
  );
}
