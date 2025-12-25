
import './ExchangeTypeToggle.css';

interface ExchangeTypeToggleProps {
  value: 'fixed' | 'float';
  onChange: (value: 'fixed' | 'float') => void;
}

export function ExchangeTypeToggle({ value, onChange }: ExchangeTypeToggleProps) {
  return (
    <div className="exchange-type-toggle">
      <button
        className={`exchange-type-option ${value === 'fixed' ? 'active' : ''}`}
        onClick={() => onChange('fixed')}
      >
        <span className="exchange-type-icon">🔒</span>
        <div className="exchange-type-content">
          <span className="exchange-type-name">Фиксированный</span>
          <span className="exchange-type-desc">Курс гарантирован</span>
        </div>
      </button>
      
      <button
        className={`exchange-type-option ${value === 'float' ? 'active' : ''}`}
        onClick={() => onChange('float')}
      >
        <span className="exchange-type-icon">📈</span>
        <div className="exchange-type-content">
          <span className="exchange-type-name">Плавающий</span>
          <span className="exchange-type-desc">Лучший курс</span>
        </div>
      </button>
    </div>
  );
}
