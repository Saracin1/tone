import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export default function Login() {
  const navigate = useNavigate();
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const response = await fetch(`${BACKEND_URL}/api/auth/me`, {
          credentials: 'include'
        });
        if (response.ok) {
          const user = await response.json();
          if (user.role === 'admin') {
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
    const redirectUrl = window.location.origin + '/dashboard';
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  if (checking) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">جاري التحميل...</p>
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
      
      <div className="relative z-10 w-full max-w-md mx-4">
        <div className="bg-card/60 backdrop-blur-md border border-border/50 rounded-xl shadow-2xl p-8">
          <div className="text-center mb-8">
            <div 
              className="w-20 h-20 mx-auto mb-4 bg-cover bg-center rounded-full border-4 border-primary/20"
              style={{ backgroundImage: "url('https://images.unsplash.com/photo-1613982102700-e8715e4f472e?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NjZ8MHwxfHNlYXJjaHwzfHxhcmFiaWMlMjBmbG9yYWwlMjBvcm5hbWVudCUyMHZlY3RvciUyMHN0eWxlfGVufDB8fHx8MTc2NzQ0OTA2MHww&ixlib=rb-4.1.0&q=85')" }}
            ></div>
            <h1 className="text-4xl font-bold mb-2 text-foreground">الواحة المالية</h1>
            <p className="text-muted-foreground text-lg">منصة التحليل المالي</p>
          </div>
          
          <div className="space-y-4">
            <p className="text-center text-sm text-muted-foreground">
              تحليلات مالية متقدمة للأسواق الخليجية والعربية
            </p>
            
            <Button 
              onClick={handleLogin}
              className="w-full bg-primary hover:bg-primary/90 text-primary-foreground rounded-full py-6 text-lg font-medium transition-all shadow-lg hover:shadow-xl"
              data-testid="login-button"
            >
              تسجيل الدخول عبر Google
            </Button>
            
            <p className="text-xs text-center text-muted-foreground mt-4">
              بالتسجيل، أنت توافق على شروط الخدمة وسياسة الخصوصية
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
