import { useSubscription } from '@/contexts/SubscriptionContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AlertCircle, CheckCircle, XCircle, Clock } from 'lucide-react';

export function SubscriptionBanner() {
  const { subscriptionStatus, loading } = useSubscription();
  const { t, language } = useLanguage();

  if (loading || !subscriptionStatus) return null;

  const { subscription_status, subscription_type, has_access, days_remaining } = subscriptionStatus;

  if (subscription_status === 'active' && has_access) {
    return (
      <Card className="bg-primary/10 border-primary/20 p-3 mb-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-primary" />
            <span className="font-medium text-sm">
              {language === 'ar' ? `اشتراك ${subscription_type} نشط` : `${subscription_type} Subscription Active`}
            </span>
          </div>
          {days_remaining !== null && (
            <Badge variant="outline" className="gap-1">
              <Clock className="w-3 h-3" />
              {days_remaining} {language === 'ar' ? 'يوم متبقي' : 'days left'}
            </Badge>
          )}
        </div>
      </Card>
    );
  }

  if (subscription_status === 'expired') {
    return (
      <Card className="bg-destructive/10 border-destructive/20 p-3 mb-4">
        <div className="flex items-center gap-2">
          <XCircle className="w-5 h-5 text-destructive" />
          <span className="font-medium text-sm">
            {language === 'ar' ? 'انتهى الاشتراك - الوصول محدود' : 'Subscription Expired - Limited Access'}
          </span>
        </div>
      </Card>
    );
  }

  return (
    <Card className="bg-muted/50 border-border p-3 mb-4">
      <div className="flex items-center gap-2">
        <AlertCircle className="w-5 h-5 text-muted-foreground" />
        <span className="font-medium text-sm">
          {language === 'ar' ? 'لا يوجد اشتراك - الوصول محدود' : 'No Subscription - Limited Access'}
        </span>
      </div>
    </Card>
  );
}
