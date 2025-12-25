
import { Loader } from '../common';
import type { ExchangeRate as ExchangeRateType, Currency } from '../../types';
import './ExchangeRate.css';

interface ExchangeRateProps {
  rate: ExchangeRateType | null;
  fromCurrency: Currency | null;
  toCurrency: Currency | null;
  isLoading?: boolean;
}

export function ExchangeRate({
  rate,
  fromCurrency,
  toCurrency,
  isLoading = false,
}: ExchangeRateProps) {
  if (isLoading) {
    return (
      <div className="exchange-rate exchange-rate-loading">
        <Loader size="small" />
        <span>Расчёт курса...</span>
      </div>
    );
  }
  
  if (!rate || !fromCurrency || !toCurrency) {
    return null;
  }
  
  const hasErrors = rate.errors && rate.errors.length > 0;
  
  return (
    <div className={`exchange-rate ${hasErrors ? 'exchange-rate-error' : ''}`}>
      <div className="exchange-rate-header">
        <span className="exchange-rate-label">Вы получите</span>
        {rate.to.rate && (
          <span className="exchange-rate-value">
            1 {fromCurrency.code} ≈ {parseFloat(rate.to.rate).toFixed(6)} {toCurrency.code}
          </span>
        )}
      </div>
      
      <div className="exchange-rate-amount">
        <span className="exchange-rate-number">
          {formatAmount(rate.to.amount)}
        </span>
        <span className="exchange-rate-currency">{toCurrency.code}</span>
      </div>
      
      {hasErrors && (
        <div className="exchange-rate-errors">
          {rate.errors!.map((error, index) => (
            <span key={index} className="exchange-rate-error-text">
              ⚠️ {error}
            </span>
          ))}
        </div>
      )}
      
      <div className="exchange-rate-info">
        <div className="exchange-rate-info-item">
          <span>Комиссия сети</span>
          <span>Включена</span>
        </div>
        <div className="exchange-rate-info-item">
          <span>Время обмена</span>
          <span>~5-30 мин</span>
        </div>
      </div>
    </div>
  );
}

function formatAmount(amount: string): string {
  const num = parseFloat(amount);
  if (isNaN(num)) return '0';
  
  if (num < 0.00001) {
    return num.toExponential(4);
  }
  
  if (num < 1) {
    return num.toFixed(8).replace(/\.?0+$/, '');
  }
  
  if (num < 1000) {
    return num.toFixed(6).replace(/\.?0+$/, '');
  }
  
  return num.toLocaleString('en-US', { maximumFractionDigits: 2 });
}
