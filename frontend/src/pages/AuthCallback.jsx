import { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useLanguage } from '@/contexts/LanguageContext';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export default function AuthCallback() {
  const navigate = useNavigate();
  const { t } = useLanguage();
  const hasProcessed = useRef(false);

  useEffect(() => {
    if (hasProcessed.current) return;
    hasProcessed.current = true;

    const processSession = async () => {
      const hash = window.location.hash;
      const sessionId = new URLSearchParams(hash.substring(1)).get('session_id');

      if (!sessionId) {
        navigate('/');
        return;
      }

      try {
        const response = await fetch(`${BACKEND_URL}/api/auth/session`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({ session_id: sessionId })
        });

        if (!response.ok) throw new Error('Session exchange failed');

        const user = await response.json();
        
        if (user.access_level === 'admin') {
          navigate('/admin', { state: { user }, replace: true });
        } else {
          navigate('/dashboard', { state: { user }, replace: true });
        }
      } catch (error) {
        console.error('Auth error:', error);
        navigate('/');
      }
    };

    processSession();
  }, [navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
        <p className="mt-4 text-muted-foreground">{t('authenticating')}</p>
      </div>
    </div>
  );
}
