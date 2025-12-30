import React, { useState, useMemo } from 'react';
import { Modal, Input } from '../common';
import type { Currency } from '../../types';
import './CurrencyInput.css';

interface CurrencyInputProps {
  label: string;
  amount: string;
  onAmountChange: (value: string) => void;
  currencies: Currency[];
  selectedCurrency: Currency | null;
  onCurrencySelect: (currency: Currency) => void;
  disabled?: boolean;
  readOnly?: boolean;
  showMax?: boolean;
  minAmount?: number;
  maxAmount?: number;
}

export function CurrencyInput({
  label,
  amount,
  onAmountChange,
  currencies,
  selectedCurrency,
  onCurrencySelect,
  disabled = false,
  readOnly = false,
  showMax = true,
  minAmount,
  maxAmount,
}: CurrencyInputProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [search, setSearch] = useState('');
  
  const filteredCurrencies = useMemo(() => {
    if (!search) return currencies;
    const query = search.toLowerCase();
    return currencies.filter(c => 
      c.code.toLowerCase().includes(query) ||
      c.name.toLowerCase().includes(query) ||
      c.network.toLowerCase().includes(query)
    );
  }, [currencies, search]);
  
  const handleAmountChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    if (/^\d*\.?\d*$/.test(newValue)) {
      onAmountChange(newValue);
    }
  };
  
  const handleMax = () => {
    if (maxAmount) {
      onAmountChange(String(maxAmount));
    } else if (selectedCurrency?.max) {
      onAmountChange(String(selectedCurrency.max));
    }
  };
  
  const handleCurrencySelect = (currency: Currency) => {
    onCurrencySelect(currency);
    setIsModalOpen(false);
    setSearch('');
  };
  
  const displayMin = minAmount ?? selectedCurrency?.min;
  const displayMax = maxAmount ?? selectedCurrency?.max;
  
  return (
    <>
      <div className={`currency-input ${disabled ? 'currency-input--disabled' : ''}`}>
        <div className="currency-input__header">
          <span className="currency-input__label">{label}</span>
          {displayMin !== undefined && displayMax !== undefined && (
            <span className="currency-input__limits">
              {displayMin.toFixed(4)} - {displayMax.toFixed(4)}
            </span>
          )}
        </div>
        
        <div className="currency-input__body">
          <div className="currency-input__amount-section">
            <input
              type="text"
              inputMode="decimal"
              value={amount}
              onChange={handleAmountChange}
              placeholder="0"
              disabled={disabled || !selectedCurrency}
              readOnly={readOnly}
              className="currency-input__field"
            />
          </div>
          
          <div className="currency-input__currency-section">
            <button 
              className="currency-input__selector"
              onClick={() => !disabled && setIsModalOpen(true)}
              disabled={disabled}
            >
              {selectedCurrency ? (
                <>
                  <span className="currency-input__icon">
                    {getCurrencyIcon(selectedCurrency.code)}
                  </span>
                  <div className="currency-input__currency-info">
                    <span className="currency-input__code">{selectedCurrency.code}</span>
                    <span className="currency-input__network">{selectedCurrency.network}</span>
                  </div>
                  <span className="currency-input__chevron">▼</span>
                </>
              ) : (
                <>
                  <span className="currency-input__placeholder">Выбрать</span>
                  <span className="currency-input__chevron">▼</span>
                </>
              )}
            </button>
            
            {showMax && !readOnly && selectedCurrency && (
              <button 
                className="currency-input__max"
                onClick={handleMax}
                disabled={disabled}
              >
                MAX
              </button>
            )}
          </div>
        </div>
      </div>
      
      <Modal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setSearch('');
        }}
        title="Выберите валюту"
      >
        <div className="currency-input__search">
          <Input
            value={search}
            onChange={setSearch}
            placeholder="Поиск по названию или коду..."
          />
        </div>
        
        <div className="currency-input__list">
          {filteredCurrencies.length === 0 ? (
            <div className="currency-input__empty">Валюты не найдены</div>
          ) : (
            filteredCurrencies.map((currency, index) => (
              <button
                key={`${currency.code}-${currency.network}-${index}`}
                className={`currency-input__item ${
                  selectedCurrency?.code === currency.code && 
                  selectedCurrency?.network === currency.network 
                    ? 'currency-input__item--selected' 
                    : ''
                }`}
                onClick={() => handleCurrencySelect(currency)}
              >
                <span className="currency-input__item-icon">
                  {getCurrencyIcon(currency.code)}
                </span>
                <div className="currency-input__item-details">
                  <span className="currency-input__item-code">{currency.code}</span>
                  <span className="currency-input__item-name">{currency.name}</span>
                </div>
                <span className="currency-input__item-network">{currency.network}</span>
              </button>
            ))
          )}
        </div>
      </Modal>
    </>
  );
}

function getCurrencyIcon(code: string): string {
  const icons: Record<string, string> = {
    BTC: '₿',
    ETH: 'Ξ',
    USDT: '₮',
    USDC: '$',
    BNB: 'B',
    SOL: '◎',
    XRP: '✕',
    DOGE: 'Ð',
    LTC: 'Ł',
    TRX: 'T',
    ADA: '₳',
    DOT: '●',
    MATIC: 'M',
    AVAX: 'A',
    LINK: '⬡',
  };
  return icons[code] || code.charAt(0);
}
