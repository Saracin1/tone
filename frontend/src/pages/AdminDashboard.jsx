import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { toast } from 'sonner';
import { LogOut, Plus } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export default function AdminDashboard() {
  const navigate = useNavigate();
  const location = useLocation();
  const [user, setUser] = useState(location.state?.user || null);
  const [isAuthenticated, setIsAuthenticated] = useState(location.state?.user ? true : null);
  const [markets, setMarkets] = useState([]);
  const [assets, setAssets] = useState([]);

  useEffect(() => {
    if (location.state?.user) return;
    
    const checkAuth = async () => {
      try {
        const response = await fetch(`${BACKEND_URL}/api/auth/me`, {
          credentials: 'include'
        });
        if (!response.ok) throw new Error('Not authenticated');
        const userData = await response.json();
        if (userData.role !== 'admin') {
          navigate('/dashboard');
          return;
        }
        setUser(userData);
        setIsAuthenticated(true);
      } catch (error) {
        setIsAuthenticated(false);
        navigate('/');
      }
    };
    checkAuth();
  }, [navigate, location.state]);

  useEffect(() => {
    if (isAuthenticated) {
      fetchMarkets();
      fetchAssets();
    }
  }, [isAuthenticated]);

  const fetchMarkets = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/markets`, {
        credentials: 'include'
      });
      const data = await response.json();
      setMarkets(data);
    } catch (error) {
      console.error('Error fetching markets:', error);
    }
  };

  const fetchAssets = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/assets`, {
        credentials: 'include'
      });
      const data = await response.json();
      setAssets(data);
    } catch (error) {
      console.error('Error fetching assets:', error);
    }
  };

  const handleLogout = async () => {
    try {
      await fetch(`${BACKEND_URL}/api/auth/logout`, {
        method: 'POST',
        credentials: 'include'
      });
      navigate('/');
    } catch (error) {
      console.error('Logout error:', error);
    }
  };

  const handleCreateMarket = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    try {
      const response = await fetch(`${BACKEND_URL}/api/markets`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          name_ar: formData.get('name_ar'),
          name_en: formData.get('name_en'),
          region: formData.get('region')
        })
      });
      if (response.ok) {
        toast.success('تم إنشاء السوق بنجاح');
        fetchMarkets();
        e.target.reset();
      }
    } catch (error) {
      toast.error('فشل إنشاء السوق');
    }
  };

  const handleCreateAsset = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    try {
      const response = await fetch(`${BACKEND_URL}/api/assets`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          market_id: formData.get('market_id'),
          name_ar: formData.get('name_ar'),
          name_en: formData.get('name_en'),
          type: formData.get('type')
        })
      });
      if (response.ok) {
        toast.success('تم إنشاء الأصل بنجاح');
        fetchAssets();
        e.target.reset();
      }
    } catch (error) {
      toast.error('فشل إنشاء الأصل');
    }
  };

  const handleCreateAnalysis = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    try {
      const response = await fetch(`${BACKEND_URL}/api/analysis`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          asset_id: formData.get('asset_id'),
          bias: formData.get('bias'),
          key_levels: formData.get('key_levels'),
          scenario_text: formData.get('scenario_text'),
          insight_text: formData.get('insight_text'),
          risk_note: formData.get('risk_note'),
          confidence_level: formData.get('confidence_level')
        })
      });
      if (response.ok) {
        toast.success('تم إنشاء التحليل بنجاح');
        e.target.reset();
      }
    } catch (error) {
      toast.error('فشل إنشاء التحليل');
    }
  };

  if (isAuthenticated === null) {
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
    <div className="min-h-screen bg-background">
      <header className="border-b border-border/50 bg-card/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-foreground">لوحة تحكم المدير</h1>
          <div className="flex items-center gap-4">
            <span className="text-sm text-muted-foreground">{user?.name}</span>
            <Button
              onClick={handleLogout}
              variant="ghost"
              size="sm"
              className="gap-2"
              data-testid="logout-button"
            >
              <LogOut className="w-4 h-4" />
              تسجيل الخروج
            </Button>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <Tabs defaultValue="markets" className="w-full" dir="rtl">
          <TabsList className="grid w-full grid-cols-3 mb-8">
            <TabsTrigger value="markets" data-testid="markets-tab">الأسواق</TabsTrigger>
            <TabsTrigger value="assets" data-testid="assets-tab">الأصول</TabsTrigger>
            <TabsTrigger value="analysis" data-testid="analysis-tab">التحليلات</TabsTrigger>
          </TabsList>

          <TabsContent value="markets">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Plus className="w-5 h-5" />
                    إضافة سوق جديد
                  </CardTitle>
                  <CardDescription>أضف سوق مالي جديد للمنصة</CardDescription>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleCreateMarket} className="space-y-4">
                    <div>
                      <Label htmlFor="name_ar">الاسم بالعربية</Label>
                      <Input id="name_ar" name="name_ar" required className="text-right" />
                    </div>
                    <div>
                      <Label htmlFor="name_en">الاسم بالإنجليزية</Label>
                      <Input id="name_en" name="name_en" required className="text-right" />
                    </div>
                    <div>
                      <Label htmlFor="region">المنطقة</Label>
                      <Input id="region" name="region" required className="text-right" placeholder="مثال: الخليج، اسطنبول، القاهرة" />
                    </div>
                    <Button type="submit" className="w-full" data-testid="create-market-button">
                      إنشاء السوق
                    </Button>
                  </form>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>الأسواق الحالية</CardTitle>
                  <CardDescription>قائمة الأسواق المتاحة</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3" data-testid="markets-list">
                    {markets.length === 0 ? (
                      <p className="text-muted-foreground text-center py-8">لا توجد أسواق بعد</p>
                    ) : (
                      markets.map((market) => (
                        <div key={market.market_id} className="p-4 border border-border rounded-lg">
                          <h3 className="font-semibold text-foreground">{market.name_ar}</h3>
                          <p className="text-sm text-muted-foreground">{market.name_en}</p>
                          <p className="text-xs text-muted-foreground mt-1">المنطقة: {market.region}</p>
                        </div>
                      ))
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="assets">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Plus className="w-5 h-5" />
                    إضافة أصل جديد
                  </CardTitle>
                  <CardDescription>أضف سهم أو مؤشر جديد</CardDescription>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleCreateAsset} className="space-y-4">
                    <div>
                      <Label htmlFor="asset_market_id">السوق</Label>
                      <select
                        id="asset_market_id"
                        name="market_id"
                        required
                        className="w-full px-3 py-2 border border-input rounded-md bg-background text-right"
                      >
                        <option value="">اختر السوق</option>
                        {markets.map((market) => (
                          <option key={market.market_id} value={market.market_id}>
                            {market.name_ar}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <Label htmlFor="asset_name_ar">الاسم بالعربية</Label>
                      <Input id="asset_name_ar" name="name_ar" required className="text-right" />
                    </div>
                    <div>
                      <Label htmlFor="asset_name_en">الاسم بالإنجليزية</Label>
                      <Input id="asset_name_en" name="name_en" required className="text-right" />
                    </div>
                    <div>
                      <Label htmlFor="asset_type">النوع</Label>
                      <select
                        id="asset_type"
                        name="type"
                        required
                        className="w-full px-3 py-2 border border-input rounded-md bg-background text-right"
                      >
                        <option value="stock">سهم</option>
                        <option value="index">مؤشر</option>
                      </select>
                    </div>
                    <Button type="submit" className="w-full" data-testid="create-asset-button">
                      إنشاء الأصل
                    </Button>
                  </form>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>الأصول الحالية</CardTitle>
                  <CardDescription>قائمة الأصول المتاحة</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3 max-h-[500px] overflow-y-auto" data-testid="assets-list">
                    {assets.length === 0 ? (
                      <p className="text-muted-foreground text-center py-8">لا توجد أصول بعد</p>
                    ) : (
                      assets.map((asset) => (
                        <div key={asset.asset_id} className="p-4 border border-border rounded-lg">
                          <h3 className="font-semibold text-foreground">{asset.name_ar}</h3>
                          <p className="text-sm text-muted-foreground">{asset.name_en}</p>
                          <p className="text-xs text-muted-foreground mt-1">
                            النوع: {asset.type === 'stock' ? 'سهم' : 'مؤشر'}
                          </p>
                        </div>
                      ))
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="analysis">
            <Card className="max-w-2xl mx-auto">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Plus className="w-5 h-5" />
                  إضافة تحليل جديد
                </CardTitle>
                <CardDescription>أضف أو حدّث تحليل لأصل معين</CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleCreateAnalysis} className="space-y-4">
                  <div>
                    <Label htmlFor="analysis_asset_id">الأصل</Label>
                    <select
                      id="analysis_asset_id"
                      name="asset_id"
                      required
                      className="w-full px-3 py-2 border border-input rounded-md bg-background text-right"
                    >
                      <option value="">اختر الأصل</option>
                      {assets.map((asset) => (
                        <option key={asset.asset_id} value={asset.asset_id}>
                          {asset.name_ar}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <Label htmlFor="bias">التوجه</Label>
                    <Input id="bias" name="bias" required className="text-right" placeholder="مثال: صاعد، هابط، محايد" />
                  </div>
                  <div>
                    <Label htmlFor="key_levels">المستويات الرئيسية</Label>
                    <Textarea id="key_levels" name="key_levels" required className="text-right" placeholder="دعم: 100، مقاومة: 120، هدف: 130" rows={3} />
                  </div>
                  <div>
                    <Label htmlFor="scenario_text">السيناريو</Label>
                    <Textarea id="scenario_text" name="scenario_text" required className="text-right" placeholder="وصف السيناريو المتوقع..." rows={4} />
                  </div>
                  <div>
                    <Label htmlFor="insight_text">ملاحظات الإطار الزمني الأعلى (اختياري)</Label>
                    <Textarea id="insight_text" name="insight_text" className="text-right" placeholder="ملاحظات إضافية..." rows={3} />
                  </div>
                  <div>
                    <Label htmlFor="risk_note">ملاحظة المخاطر (اختياري)</Label>
                    <Textarea id="risk_note" name="risk_note" className="text-right" placeholder="تحذيرات أو مخاطر محتملة..." rows={2} />
                  </div>
                  <div>
                    <Label htmlFor="confidence_level">مستوى الثقة</Label>
                    <select
                      id="confidence_level"
                      name="confidence_level"
                      required
                      className="w-full px-3 py-2 border border-input rounded-md bg-background text-right"
                    >
                      <option value="Low">منخفض</option>
                      <option value="Medium">متوسط</option>
                      <option value="High">عالي</option>
                    </select>
                  </div>
                  <Button type="submit" className="w-full" data-testid="create-analysis-button">
                    نشر التحليل
                  </Button>
                </form>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
