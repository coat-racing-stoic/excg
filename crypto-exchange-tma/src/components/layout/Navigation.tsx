
import { useNavigate, useLocation } from 'react-router-dom';
import './Navigation.css';

interface NavItem {
  path: string;
  label: string;
  icon: string;
}

const navItems: NavItem[] = [
  { path: '/', label: 'Обмен', icon: '💱' },
  { path: '/history', label: 'История', icon: '📋' },
];

export function Navigation() {
  const navigate = useNavigate();
  const location = useLocation();
  
  return (
    <nav className="navigation">
      {navItems.map((item) => (
        <button
          key={item.path}
          className={`nav-item ${location.pathname === item.path ? 'active' : ''}`}
          onClick={() => navigate(item.path)}
        >
          <span className="nav-icon">{item.icon}</span>
          <span className="nav-label">{item.label}</span>
        </button>
      ))}
    </nav>
  );
}
