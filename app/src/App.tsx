import { BrowserRouter, Route, Routes } from 'react-router';
import Landing from '@/pages/Landing';
import Chat from '@/pages/Chat';
import Admin from '@/pages/Admin';
import Dashboard from '@/pages/Dashboard';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/chat" element={<Chat />} />
        <Route path="/admin" element={<Admin />} />
      </Routes>
    </BrowserRouter>
  );
}
