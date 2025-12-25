
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { HomePage, OrderPage, HistoryPage } from './pages';

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/order/:orderId" element={<OrderPage />} />
        <Route path="/history" element={<HistoryPage />} />
      </Routes>
    </BrowserRouter>
  );
}
