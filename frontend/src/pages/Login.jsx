import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useLanguage } from '@/contexts/LanguageContext';
import { Button } from '@/components/ui/button';
import { LanguageSwitcher } from '@/components/LanguageSwitcher';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const LOGO_URL = 'https://customer-assets.emergentagent.com/job_8e72d90b-2ff6-41c5-81dc-28aaecc4e8af/artifacts/auvyrao6_ChatGPT%20Image%20Jan%207%2C%202026%2C%2010_00_13%20PM.png';

export default function Login() {
  const navigate = useNavigate();
  const { t } = useLanguage();
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const response = await fetch(`${BACKEND_URL}/api/auth/me`, {
          credentials: 'include'
        });
        if (response.ok) {
          const user = await response.json();
          if (user.access_level === 'admin') {
            navigate('/admin');
          } else {
            navigate('/dashboard');
          }
        }
      } catch (error) {
        console.log('Not authenticated');
      } finally {
        setChecking(false);
      }
    };
    checkAuth();
  }, [navigate]);

  const handleLogin = () => {
    // Direct to backend Google OAuth endpoint
    window.location.href = `${BACKEND_URL}/api/auth/google`;
  };

  if (checking) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">{t('loading')}</p>
        </div>
      </div>
    );
  }

  return (
    <div 
      className="min-h-screen flex items-center justify-center bg-cover bg-center relative"
      style={{ backgroundImage: "url('https://images.unsplash.com/photo-1680214180543-119d7f766381?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2Mzl8MHwxfHNlYXJjaHwxfHxkZXNlcnQlMjBzYW5kJTIwdGV4dHVyZSUyMGxpZ2h0JTIwc3VidGxlfGVufDB8fHx8MTc2NzQ0OTA1OHww&ixlib=rb-4.1.0&q=85')" }}
    >
      <div className="absolute inset-0 bg-background/80 backdrop-blur-sm"></div>
      
      <div className="absolute top-4 right-4 z-50">
        <LanguageSwitcher />
      </div>
      
      <div className="relative z-10 w-full max-w-md mx-4">
        <div className="bg-card/60 backdrop-blur-md border border-border/50 rounded-xl shadow-2xl p-8">
          <div className="text-center mb-8">
            <img 
              src={LOGO_URL}
              alt="Tahlil One Logo"
              className="w-64 h-auto mx-auto mb-6"
            />
            <p className="text-muted-foreground text-lg">{t('appTagline')}</p>
          </div>
          
          <div className="space-y-4">
            <p className="text-center text-sm text-muted-foreground">
              {t('appDescription')}
            </p>
            
            <Button 
              onClick={handleLogin}
              className="w-full bg-primary hover:bg-primary/90 text-primary-foreground rounded-full py-6 text-lg font-medium transition-all shadow-lg hover:shadow-xl"
              data-testid="login-button"
            >
              {t('loginButton')}
            </Button>
            
            <p className="text-xs text-center text-muted-foreground mt-4">
              {t('loginDisclaimer')}
            </p>
          </div>
        </div>
        
        <div 
          className="absolute -top-10 -right-10 w-32 h-32 bg-primary/10 rounded-full blur-3xl"
        ></div>
        <div 
          className="absolute -bottom-10 -left-10 w-40 h-40 bg-secondary/20 rounded-full blur-3xl"
        ></div>
      </div>
    </div>
  );
}
