import React from 'react';
import type { Currency } from '../../types';
import './AmountInput.css';

interface AmountInputProps {
  value: string;
  onChange: (value: string) => void;
  currency: Currency | null;
  label?: string;
  disabled?: boolean;
  readOnly?: boolean;
}

export function AmountInput({
  value,
  onChange,
  currency,
  label = 'Сумма',
  disabled = false,
  readOnly = false,
}: AmountInputProps) {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    // Allow only numbers and one decimal point
    if (/^\d*\.?\d*$/.test(newValue)) {
      onChange(newValue);
    }
  };
  
  const handleMax = () => {
    if (currency?.max) {
      onChange(String(currency.max));
    }
  };
  
  return (
    <div className="amount-input">
      <div className="amount-input-header">
        <span className="amount-input-label">{label}</span>
        {currency && (
          <span className="amount-input-limits">
            Мин: {currency.min} | Макс: {currency.max}
          </span>
        )}
      </div>
      <div className="amount-input-container">
        <input
          type="text"
          inputMode="decimal"
          value={value}
          onChange={handleChange}
          placeholder="0.00"
          disabled={disabled}
          readOnly={readOnly}
          className="amount-input-field"
        />
        {currency && (
          <div className="amount-input-suffix">
            <span className="amount-input-currency">{currency.code}</span>
            {!readOnly && (
              <button 
                className="amount-input-max"
                onClick={handleMax}
                disabled={disabled}
              >
                MAX
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
