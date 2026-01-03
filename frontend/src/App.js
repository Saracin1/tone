import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom';
import Login from '@/pages/Login';
import AuthCallback from '@/pages/AuthCallback';
import AdminDashboard from '@/pages/AdminDashboard';
import UserDashboard from '@/pages/UserDashboard';
import { Toaster } from '@/components/ui/sonner';

function AppRouter() {
  const location = useLocation();
  if (location.hash?.includes('session_id=')) {
    return <AuthCallback />;
  }
  return (
    <Routes>
      <Route path="/" element={<Login />} />
      <Route path="/admin" element={<AdminDashboard />} />
      <Route path="/dashboard" element={<UserDashboard />} />
    </Routes>
  );
}

function App() {
  return (
    <div className="App" dir="rtl">
      <BrowserRouter>
        <AppRouter />
      </BrowserRouter>
      <Toaster />
    </div>
  );
}

export default App;
