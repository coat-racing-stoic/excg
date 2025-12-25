import React from 'react';
import './Input.css';

interface InputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  type?: 'text' | 'number' | 'email';
  label?: string;
  error?: string;
  disabled?: boolean;
  suffix?: React.ReactNode;
  prefix?: React.ReactNode;
}

export function Input({
  value,
  onChange,
  placeholder,
  type = 'text',
  label,
  error,
  disabled = false,
  suffix,
  prefix,
}: InputProps) {
  return (
    <div className={`input-wrapper ${error ? 'input-error' : ''}`}>
      {label && <label className="input-label">{label}</label>}
      <div className="input-container">
        {prefix && <span className="input-prefix">{prefix}</span>}
        <input
          type={type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          disabled={disabled}
          className="input-field"
        />
        {suffix && <span className="input-suffix">{suffix}</span>}
      </div>
      {error && <span className="input-error-text">{error}</span>}
    </div>
  );
}
