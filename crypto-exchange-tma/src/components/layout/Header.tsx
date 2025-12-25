
import { useTelegram } from '../../hooks';
import './Header.css';

interface HeaderProps {
  title?: string;
  subtitle?: string;
}

export function Header({ title = 'Crypto Exchange', subtitle }: HeaderProps) {
  const { user } = useTelegram();
  
  return (
    <header className="header">
      <div className="header-content">
        <div className="header-info">
          <h1 className="header-title">{title}</h1>
          {subtitle && <p className="header-subtitle">{subtitle}</p>}
        </div>
        
        {user && (
          <div className="header-user">
            <span className="header-user-name">
              {user.firstName}
            </span>
          </div>
        )}
      </div>
    </header>
  );
}
