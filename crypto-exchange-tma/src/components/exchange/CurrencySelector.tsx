import { useState, useMemo } from 'react';
import { Modal, Input } from '../common';
import type { Currency } from '../../types';
import './CurrencySelector.css';

interface CurrencySelectorProps {
  label: string;
  currencies: Currency[];
  selected: Currency | null;
  onSelect: (currency: Currency) => void;
  disabled?: boolean;
}

export function CurrencySelector({
  label,
  currencies,
  selected,
  onSelect,
  disabled = false,
}: CurrencySelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
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
  
  const handleSelect = (currency: Currency) => {
    onSelect(currency);
    setIsOpen(false);
    setSearch('');
  };
  
  return (
    <>
      <div className="currency-selector">
        <span className="currency-selector-label">{label}</span>
        <button 
          className="currency-selector-button"
          onClick={() => !disabled && setIsOpen(true)}
          disabled={disabled}
        >
          {selected ? (
            <>
              <span className="currency-icon">{getCurrencyIcon(selected.code)}</span>
              <div className="currency-info">
                <span className="currency-code">{selected.code}</span>
                <span className="currency-network">{selected.network}</span>
              </div>
              <span className="currency-chevron">›</span>
            </>
          ) : (
            <>
              <span className="currency-placeholder">Выберите валюту</span>
              <span className="currency-chevron">›</span>
            </>
          )}
        </button>
      </div>
      
      <Modal
        isOpen={isOpen}
        onClose={() => {
          setIsOpen(false);
          setSearch('');
        }}
        title="Выберите валюту"
      >
        <div className="currency-search">
          <Input
            value={search}
            onChange={setSearch}
            placeholder="Поиск по названию или коду..."
          />
        </div>
        
        <div className="currency-list">
          {filteredCurrencies.length === 0 ? (
            <div className="currency-empty">Валюты не найдены</div>
          ) : (
            filteredCurrencies.map((currency, index) => (
              <button
                key={`${currency.code}-${currency.network}-${index}`}
                className={`currency-item ${
                  selected?.code === currency.code && 
                  selected?.network === currency.network 
                    ? 'currency-item-selected' 
                    : ''
                }`}
                onClick={() => handleSelect(currency)}
              >
                <span className="currency-icon">{getCurrencyIcon(currency.code)}</span>
                <div className="currency-details">
                  <span className="currency-code">{currency.code}</span>
                  <span className="currency-name">{currency.name}</span>
                </div>
                <span className="currency-network-badge">{currency.network}</span>
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
