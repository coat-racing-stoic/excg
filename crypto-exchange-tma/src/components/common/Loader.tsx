
import './Loader.css';

interface LoaderProps {
  size?: 'small' | 'medium' | 'large';
  text?: string;
}

export function Loader({ size = 'medium', text }: LoaderProps) {
  return (
    <div className={`loader-container loader-${size}`}>
      <div className="loader-spinner" />
      {text && <p className="loader-text">{text}</p>}
    </div>
  );
}
