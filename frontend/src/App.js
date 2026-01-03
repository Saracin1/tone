import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom';
import { LanguageProvider, useLanguage } from '@/contexts/LanguageContext';
import Login from '@/pages/Login';
import AuthCallback from '@/pages/AuthCallback';
import AdminDashboard from '@/pages/AdminDashboard';
import UserDashboard from '@/pages/UserDashboard';
import { Toaster } from '@/components/ui/sonner';

function AppRouter() {
  const location = useLocation();
  const { language } = useLanguage();
  
  if (location.hash?.includes('session_id=')) {
    return <AuthCallback />;
  }
  return (
    <div dir={language === 'ar' ? 'rtl' : 'ltr'}>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/admin" element={<AdminDashboard />} />
        <Route path="/dashboard" element={<UserDashboard />} />
      </Routes>
    </div>
  );
}

function App() {
  return (
    <LanguageProvider>
      <div className="App">
        <BrowserRouter>
          <AppRouter />
        </BrowserRouter>
        <Toaster />
      </div>
    </LanguageProvider>
  );
}

export default App;
