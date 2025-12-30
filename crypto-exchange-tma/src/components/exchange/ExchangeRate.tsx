import { Loader } from '../common';
import type { PreviewRate, Currency } from '../../types';
import './ExchangeRate.css';

interface ExchangeRateProps {
  previewRate: PreviewRate | null;
  fromCurrency: Currency | null;
  toCurrency: Currency | null;
  isLoading?: boolean;
}

export function ExchangeRate({
  previewRate,
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
  
  if (!previewRate || !fromCurrency || !toCurrency) {
    return null;
  }
  
  return (
    <div className="exchange-rate">
      <div className="exchange-rate-header">
        <span className="exchange-rate-label">Вы получите (примерно)</span>
        <span className="exchange-rate-value">
          1 {fromCurrency.code} ≈ {formatRate(previewRate.rate)} {toCurrency.code}
        </span>
      </div>
      
      <div className="exchange-rate-amount">
        <span className="exchange-rate-number">
          {formatAmount(previewRate.toAmount)}
        </span>
        <span className="exchange-rate-currency">{toCurrency.code}</span>
      </div>
      
      <div className="exchange-rate-info">
        <div className="exchange-rate-info-item">
          <span>Комиссия сети</span>
          <span>{previewRate.fee}</span>
        </div>
        <div className="exchange-rate-info-item">
          <span>Лимиты</span>
          <span>{previewRate.minAmount} - {previewRate.maxAmount}</span>
        </div>
        <div className="exchange-rate-info-item">
          <span>Время обмена</span>
          <span>~5-30 мин</span>
        </div>
      </div>
      
      <div className="exchange-rate-source">
        <span className="exchange-rate-source-badge">
          {previewRate.source === 'cache' ? '⚡ Быстрый расчёт' : '🔄 Актуальный курс'}
        </span>
        <span className="exchange-rate-disclaimer">
          Точный курс будет рассчитан при подтверждении
        </span>
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

function formatRate(rate: number): string {
  if (rate < 0.0001) {
    return rate.toExponential(4);
  }
  if (rate < 1) {
    return rate.toFixed(8).replace(/\.?0+$/, '');
  }
  if (rate < 100) {
    return rate.toFixed(6).replace(/\.?0+$/, '');
  }
  return rate.toLocaleString('en-US', { maximumFractionDigits: 2 });
}
