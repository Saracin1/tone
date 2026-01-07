import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useLanguage } from '@/contexts/LanguageContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import { LogOut, Plus, Trophy, TrendingUp, TrendingDown, Trash2, Edit2 } from 'lucide-react';
import { LanguageSwitcher } from '@/components/LanguageSwitcher';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export default function AdminDashboard() {
  const navigate = useNavigate();
  const location = useLocation();
  const { t, language } = useLanguage();
  const [user, setUser] = useState(location.state?.user || null);
  const [isAuthenticated, setIsAuthenticated] = useState(location.state?.user ? true : null);
  const [markets, setMarkets] = useState([]);
  const [assets, setAssets] = useState([]);
  const [users, setUsers] = useState([]);
  const [selectedUser, setSelectedUser] = useState(null);
  const [syncResults, setSyncResults] = useState(null);
  const [syncing, setSyncing] = useState(false);
  const [dailyAnalysis, setDailyAnalysis] = useState([]);
  const [forecasts, setForecasts] = useState([]);
  const [editingForecast, setEditingForecast] = useState(null);

  useEffect(() => {
    if (location.state?.user) return;
    
    const checkAuth = async () => {
      try {
        const response = await fetch(`${BACKEND_URL}/api/auth/me`, {
          credentials: 'include'
        });
        if (!response.ok) throw new Error('Not authenticated');
        const userData = await response.json();
        if (userData.access_level !== 'admin') {
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
      fetchUsers();
      fetchForecasts();
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

  const fetchUsers = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/admin/users`, {
        credentials: 'include'
      });
      const data = await response.json();
      setUsers(data);
    } catch (error) {
      console.error('Error fetching users:', error);
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
        toast.success(t('marketCreated'));
        fetchMarkets();
        e.target.reset();
      }
    } catch (error) {
      toast.error(t('marketFailed'));
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
        toast.success(t('assetCreated'));
        fetchAssets();
        e.target.reset();
      }
    } catch (error) {
      toast.error(t('assetFailed'));
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
        toast.success(t('analysisCreated'));
        e.target.reset();
      }
    } catch (error) {
      toast.error(t('analysisFailed'));
    }
  };

  const handleManageSubscription = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    try {
      const response = await fetch(`${BACKEND_URL}/api/admin/users/subscription`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          user_email: formData.get('user_email'),
          subscription_type: formData.get('subscription_type'),
          duration_days: parseInt(formData.get('duration_days')),
          action: formData.get('action')
        })
      });
      if (response.ok) {
        toast.success(t('subscriptionUpdated'));
        fetchUsers();
        e.target.reset();
        setSelectedUser(null);
      } else {
        toast.error(t('subscriptionFailed'));
      }
    } catch (error) {
      toast.error(t('subscriptionFailed'));
    }
  };

  const handleSyncGoogleSheets = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    setSyncing(true);
    setSyncResults(null);
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/admin/sheets/sync`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          spreadsheet_id: formData.get('spreadsheet_id'),
          range_name: formData.get('range_name') || 'Sheet1!A2:G'
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        setSyncResults(result);
        toast.success(t('syncSuccess'));
        fetchDailyAnalysis();
      } else {
        const error = await response.json();
        toast.error(t('syncFailed') + ': ' + (error.detail || 'Unknown error'));
      }
    } catch (error) {
      toast.error(t('syncFailed'));
    } finally {
      setSyncing(false);
    }
  };

  const fetchDailyAnalysis = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/daily-analysis?limit=50`, {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        setDailyAnalysis(data);
      }
    } catch (error) {
      console.error('Error fetching daily analysis:', error);
    }
  };

  const fetchForecasts = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/admin/history/forecasts`, {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        setForecasts(data);
      }
    } catch (error) {
      console.error('Error fetching forecasts:', error);
    }
  };

  const handleCreateForecast = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    
    const forecastData = {
      instrument_code: formData.get('instrument_code'),
      market: formData.get('market'),
      forecast_date: formData.get('forecast_date'),
      forecast_direction: formData.get('forecast_direction'),
      entry_price: parseFloat(formData.get('entry_price')),
      forecast_target_price: parseFloat(formData.get('forecast_target_price')),
      notes: formData.get('notes') || null
    };

    // If actual result is provided
    const actualResult = formData.get('actual_result_price');
    const resultDate = formData.get('result_date');
    if (actualResult && resultDate) {
      forecastData.actual_result_price = parseFloat(actualResult);
      forecastData.result_date = resultDate;
    }

    try {
      const response = await fetch(`${BACKEND_URL}/api/admin/history/forecast`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(forecastData)
      });

      if (response.ok) {
        toast.success(language === 'ar' ? 'تم إنشاء التوقع بنجاح' : 'Forecast created successfully');
        fetchForecasts();
        e.target.reset();
      } else {
        const error = await response.json();
        toast.error(error.detail || (language === 'ar' ? 'فشل في إنشاء التوقع' : 'Failed to create forecast'));
      }
    } catch (error) {
      toast.error(language === 'ar' ? 'حدث خطأ' : 'An error occurred');
    }
  };

  const handleUpdateForecastResult = async (e) => {
    e.preventDefault();
    if (!editingForecast) return;
    
    const formData = new FormData(e.target);
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/admin/history/forecast/${editingForecast.record_id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          actual_result_price: parseFloat(formData.get('actual_result_price')),
          result_date: formData.get('result_date'),
          notes: formData.get('notes') || null
        })
      });

      if (response.ok) {
        toast.success(language === 'ar' ? 'تم تحديث النتيجة بنجاح' : 'Result updated successfully');
        fetchForecasts();
        setEditingForecast(null);
      } else {
        const error = await response.json();
        toast.error(error.detail || (language === 'ar' ? 'فشل في التحديث' : 'Update failed'));
      }
    } catch (error) {
      toast.error(language === 'ar' ? 'حدث خطأ' : 'An error occurred');
    }
  };

  const handleDeleteForecast = async (recordId) => {
    if (!confirm(language === 'ar' ? 'هل أنت متأكد من حذف هذا التوقع؟' : 'Are you sure you want to delete this forecast?')) {
      return;
    }

    try {
      const response = await fetch(`${BACKEND_URL}/api/admin/history/forecast/${recordId}`, {
        method: 'DELETE',
        credentials: 'include'
      });

      if (response.ok) {
        toast.success(language === 'ar' ? 'تم الحذف بنجاح' : 'Deleted successfully');
        fetchForecasts();
      } else {
        toast.error(language === 'ar' ? 'فشل في الحذف' : 'Delete failed');
      }
    } catch (error) {
      toast.error(language === 'ar' ? 'حدث خطأ' : 'An error occurred');
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    try {
      return new Date(dateStr).toLocaleDateString(language === 'ar' ? 'ar-SA' : 'en-US');
    } catch {
      return dateStr;
    }
  };

  if (isAuthenticated === null) {
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
    <div className="min-h-screen bg-background">
      <header className="border-b border-border/50 bg-card/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-foreground">{t('adminDashboard')}</h1>
          <div className="flex items-center gap-4">
            <LanguageSwitcher />
            <span className="text-sm text-muted-foreground">{user?.name}</span>
            <Button
              onClick={handleLogout}
              variant="ghost"
              size="sm"
              className="gap-2"
              data-testid="logout-button"
            >
              <LogOut className="w-4 h-4" />
              {t('logout')}
            </Button>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <Tabs defaultValue="markets" className="w-full" dir={language === 'ar' ? 'rtl' : 'ltr'}>
          <TabsList className="grid w-full grid-cols-5 mb-8">
            <TabsTrigger value="markets" data-testid="markets-tab">{t('markets')}</TabsTrigger>
            <TabsTrigger value="assets" data-testid="assets-tab">{t('assets')}</TabsTrigger>
            <TabsTrigger value="analysis" data-testid="analysis-tab">{t('analysis')}</TabsTrigger>
            <TabsTrigger value="daily" data-testid="daily-tab">{t('dailyAnalysis')}</TabsTrigger>
            <TabsTrigger value="users" data-testid="users-tab">{t('users')}</TabsTrigger>
          </TabsList>

          <TabsContent value="markets">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Plus className="w-5 h-5" />
                    {t('createMarket')}
                  </CardTitle>
                  <CardDescription>{t('createMarketDesc')}</CardDescription>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleCreateMarket} className="space-y-4">
                    <div>
                      <Label htmlFor="name_ar">{t('nameAr')}</Label>
                      <Input id="name_ar" name="name_ar" required className={language === 'ar' ? 'text-right' : ''} />
                    </div>
                    <div>
                      <Label htmlFor="name_en">{t('nameEn')}</Label>
                      <Input id="name_en" name="name_en" required className={language === 'ar' ? 'text-right' : ''} />
                    </div>
                    <div>
                      <Label htmlFor="region">{t('region')}</Label>
                      <Input id="region" name="region" required className={language === 'ar' ? 'text-right' : ''} placeholder={t('regionPlaceholder')} />
                    </div>
                    <Button type="submit" className="w-full" data-testid="create-market-button">
                      {t('createMarketButton')}
                    </Button>
                  </form>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>{t('currentMarkets')}</CardTitle>
                  <CardDescription>{t('currentMarketsDesc')}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3" data-testid="markets-list">
                    {markets.length === 0 ? (
                      <p className="text-muted-foreground text-center py-8">{t('noMarkets')}</p>
                    ) : (
                      markets.map((market) => (
                        <div key={market.market_id} className="p-4 border border-border rounded-lg">
                          <h3 className="font-semibold text-foreground">{language === 'ar' ? market.name_ar : market.name_en}</h3>
                          <p className="text-sm text-muted-foreground">{language === 'ar' ? market.name_en : market.name_ar}</p>
                          <p className="text-xs text-muted-foreground mt-1">{t('region')}: {market.region}</p>
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
                    {t('createAsset')}
                  </CardTitle>
                  <CardDescription>{t('createAssetDesc')}</CardDescription>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleCreateAsset} className="space-y-4">
                    <div>
                      <Label htmlFor="asset_market_id">{t('market')}</Label>
                      <select
                        id="asset_market_id"
                        name="market_id"
                        required
                        className={`w-full px-3 py-2 border border-input rounded-md bg-background ${language === 'ar' ? 'text-right' : ''}`}
                      >
                        <option value="">{t('selectMarket')}</option>
                        {markets.map((market) => (
                          <option key={market.market_id} value={market.market_id}>
                            {language === 'ar' ? market.name_ar : market.name_en}
                          </option>
                        ))}
                      </select>
                    </div>
                    <div>
                      <Label htmlFor="asset_name_ar">{t('nameAr')}</Label>
                      <Input id="asset_name_ar" name="name_ar" required className={language === 'ar' ? 'text-right' : ''} />
                    </div>
                    <div>
                      <Label htmlFor="asset_name_en">{t('nameEn')}</Label>
                      <Input id="asset_name_en" name="name_en" required className={language === 'ar' ? 'text-right' : ''} />
                    </div>
                    <div>
                      <Label htmlFor="asset_type">{t('type')}</Label>
                      <select
                        id="asset_type"
                        name="type"
                        required
                        className={`w-full px-3 py-2 border border-input rounded-md bg-background ${language === 'ar' ? 'text-right' : ''}`}
                      >
                        <option value="stock">{t('stock')}</option>
                        <option value="index">{t('index')}</option>
                      </select>
                    </div>
                    <Button type="submit" className="w-full" data-testid="create-asset-button">
                      {t('createAssetButton')}
                    </Button>
                  </form>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>{t('currentAssets')}</CardTitle>
                  <CardDescription>{t('currentAssetsDesc')}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3 max-h-[500px] overflow-y-auto" data-testid="assets-list">
                    {assets.length === 0 ? (
                      <p className="text-muted-foreground text-center py-8">{t('noAssets')}</p>
                    ) : (
                      assets.map((asset) => (
                        <div key={asset.asset_id} className="p-4 border border-border rounded-lg">
                          <h3 className="font-semibold text-foreground">{language === 'ar' ? asset.name_ar : asset.name_en}</h3>
                          <p className="text-sm text-muted-foreground">{language === 'ar' ? asset.name_en : asset.name_ar}</p>
                          <p className="text-xs text-muted-foreground mt-1">
                            {t('type')}: {asset.type === 'stock' ? t('stock') : t('index')}
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
                  {t('createAnalysis')}
                </CardTitle>
                <CardDescription>{t('createAnalysisDesc')}</CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleCreateAnalysis} className="space-y-4">
                  <div>
                    <Label htmlFor="analysis_asset_id">{t('asset')}</Label>
                    <select
                      id="analysis_asset_id"
                      name="asset_id"
                      required
                      className={`w-full px-3 py-2 border border-input rounded-md bg-background ${language === 'ar' ? 'text-right' : ''}`}
                    >
                      <option value="">{t('selectAsset')}</option>
                      {assets.map((asset) => (
                        <option key={asset.asset_id} value={asset.asset_id}>
                          {language === 'ar' ? asset.name_ar : asset.name_en}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <Label htmlFor="bias">{t('bias')}</Label>
                    <Input id="bias" name="bias" required className={language === 'ar' ? 'text-right' : ''} placeholder={t('biasPlaceholder')} />
                  </div>
                  <div>
                    <Label htmlFor="key_levels">{t('keyLevels')}</Label>
                    <Textarea id="key_levels" name="key_levels" required className={language === 'ar' ? 'text-right' : ''} placeholder={t('keyLevelsPlaceholder')} rows={3} />
                  </div>
                  <div>
                    <Label htmlFor="scenario_text">{t('scenario')}</Label>
                    <Textarea id="scenario_text" name="scenario_text" required className={language === 'ar' ? 'text-right' : ''} placeholder={t('scenarioPlaceholder')} rows={4} />
                  </div>
                  <div>
                    <Label htmlFor="insight_text">{t('higherTFInsight')}</Label>
                    <Textarea id="insight_text" name="insight_text" className={language === 'ar' ? 'text-right' : ''} placeholder={t('higherTFPlaceholder')} rows={3} />
                  </div>
                  <div>
                    <Label htmlFor="risk_note">{t('riskNote')}</Label>
                    <Textarea id="risk_note" name="risk_note" className={language === 'ar' ? 'text-right' : ''} placeholder={t('riskPlaceholder')} rows={2} />
                  </div>
                  <div>
                    <Label htmlFor="confidence_level">{t('confidenceLevel')}</Label>
                    <select
                      id="confidence_level"
                      name="confidence_level"
                      required
                      className={`w-full px-3 py-2 border border-input rounded-md bg-background ${language === 'ar' ? 'text-right' : ''}`}
                    >
                      <option value="Low">{t('confidenceLow')}</option>
                      <option value="Medium">{t('confidenceMedium')}</option>
                      <option value="High">{t('confidenceHigh')}</option>
                    </select>
                  </div>
                  <Button type="submit" className="w-full" data-testid="create-analysis-button">
                    {t('publishAnalysis')}
                  </Button>
                </form>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="daily">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Plus className="w-5 h-5" />
                    {t('syncFromSheets')}
                  </CardTitle>
                  <CardDescription>{t('syncFromSheetsDesc')}</CardDescription>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleSyncGoogleSheets} className="space-y-4">
                    <div>
                      <Label htmlFor="spreadsheet_id">{t('spreadsheetId')}</Label>
                      <Input 
                        id="spreadsheet_id" 
                        name="spreadsheet_id" 
                        required 
                        defaultValue="1GcXY5-SFba417vZXxOAL3uk7HZlzGBZz72-JWj2rNv4"
                        className={language === 'ar' ? 'text-right' : ''} 
                      />
                      <p className="text-xs text-muted-foreground mt-1">
                        {language === 'ar' ? 'من عنوان الرابط: docs.google.com/spreadsheets/d/[ID]' : 'From URL: docs.google.com/spreadsheets/d/[ID]'}
                      </p>
                    </div>
                    <div>
                      <Label htmlFor="range_name">{t('sheetRange')}</Label>
                      <Input 
                        id="range_name" 
                        name="range_name" 
                        defaultValue="Sheet1!A2:G"
                        className={language === 'ar' ? 'text-right' : ''} 
                      />
                      <p className="text-xs text-muted-foreground mt-1">
                        {language === 'ar' ? 'نطاق البيانات (افتراضي: Sheet1!A2:G)' : 'Data range (default: Sheet1!A2:G)'}
                      </p>
                    </div>
                    <Button 
                      type="submit" 
                      className="w-full" 
                      disabled={syncing}
                      data-testid="sync-sheets-button"
                    >
                      {syncing ? t('syncInProgress') : t('syncNow')}
                    </Button>
                  </form>

                  {syncResults && (
                    <div className="mt-6 p-4 border border-border rounded-lg space-y-2">
                      <h3 className="font-semibold text-foreground">{t('syncResults')}</h3>
                      <div className="grid grid-cols-2 gap-2 text-sm">
                        <div>
                          <span className="text-muted-foreground">{t('totalRows')}:</span>
                          <span className="font-semibold ml-2">{syncResults.total_rows}</span>
                        </div>
                        <div>
                          <span className="text-muted-foreground">{t('inserted')}:</span>
                          <span className="font-semibold ml-2 text-primary">{syncResults.inserted}</span>
                        </div>
                        <div>
                          <span className="text-muted-foreground">{t('updated')}:</span>
                          <span className="font-semibold ml-2 text-secondary">{syncResults.updated}</span>
                        </div>
                        <div>
                          <span className="text-muted-foreground">{t('skipped')}:</span>
                          <span className="font-semibold ml-2 text-muted-foreground">{syncResults.skipped}</span>
                        </div>
                      </div>
                      {syncResults.errors && syncResults.errors.length > 0 && (
                        <div className="mt-3">
                          <p className="text-sm font-semibold text-destructive mb-1">{t('errors')}:</p>
                          <div className="max-h-32 overflow-y-auto space-y-1">
                            {syncResults.errors.map((error, idx) => (
                              <p key={idx} className="text-xs text-muted-foreground">{error}</p>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>{t('latestAnalysis')}</CardTitle>
                  <CardDescription>{t('viewDailyAnalysis')}</CardDescription>
                </CardHeader>
                <CardContent>
                  <Button 
                    onClick={fetchDailyAnalysis} 
                    variant="outline" 
                    size="sm" 
                    className="mb-4"
                  >
                    {language === 'ar' ? 'تحديث' : 'Refresh'}
                  </Button>
                  <div className="space-y-3 max-h-[500px] overflow-y-auto" data-testid="daily-analysis-list">
                    {dailyAnalysis.length === 0 ? (
                      <p className="text-muted-foreground text-center py-8">
                        {language === 'ar' ? 'لا توجد تحليلات يومية بعد' : 'No daily analysis yet'}
                      </p>
                    ) : (
                      dailyAnalysis.map((record) => (
                        <div key={record.record_id} className="p-4 border border-border rounded-lg space-y-2">
                          <div className="flex items-center justify-between">
                            <h3 className="font-semibold text-foreground">{record.instrument_code}</h3>
                            <span className="text-xs text-muted-foreground">{record.market}</span>
                          </div>
                          <p className="text-sm text-primary font-medium">{record.insight_type}</p>
                          <div className="grid grid-cols-3 gap-2 text-xs text-muted-foreground">
                            <div>
                              <span className="font-semibold">{language === 'ar' ? 'السعر:' : 'Price:'}</span> {record.analysis_price}
                            </div>
                            <div>
                              <span className="font-semibold">{language === 'ar' ? 'الهدف:' : 'Target:'}</span> {record.target_price}
                            </div>
                            <div>
                              <span className="font-semibold">{language === 'ar' ? 'حرج:' : 'Critical:'}</span> {record.critical_level}
                            </div>
                          </div>
                          <p className="text-xs text-muted-foreground">
                            {new Date(record.analysis_datetime).toLocaleString(language === 'ar' ? 'ar-SA' : 'en-US')}
                          </p>
                        </div>
                      ))
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="users">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Plus className="w-5 h-5" />
                    {t('manageSubscription')}
                  </CardTitle>
                  <CardDescription>{t('activateSubscription')}, {t('extendSubscription')}, {t('giftSubscription')}</CardDescription>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleManageSubscription} className="space-y-4">
                    <div>
                      <Label htmlFor="user_email">{t('selectUser')}</Label>
                      <select
                        id="user_email"
                        name="user_email"
                        required
                        className={`w-full px-3 py-2 border border-input rounded-md bg-background ${language === 'ar' ? 'text-right' : ''}`}
                        onChange={(e) => setSelectedUser(users.find(u => u.email === e.target.value))}
                      >
                        <option value="">{t('selectUser')}</option>
                        {users.map((user) => (
                          <option key={user.user_id} value={user.email}>
                            {user.email} - {user.name}
                          </option>
                        ))}
                      </select>
                    </div>

                    {selectedUser && (
                      <div className="p-3 bg-muted rounded-lg text-sm space-y-1">
                        <p><strong>{t('subscriptionStatus')}:</strong> {selectedUser.subscription_status || t('none')}</p>
                        <p><strong>{t('subscriptionType')}:</strong> {selectedUser.subscription_type || t('none')}</p>
                        {selectedUser.subscription_end_date && (
                          <p><strong>{t('expiresOn')}:</strong> {new Date(selectedUser.subscription_end_date).toLocaleDateString(language === 'ar' ? 'ar-SA' : 'en-US')}</p>
                        )}
                      </div>
                    )}

                    <div>
                      <Label htmlFor="subscription_type_admin">{t('selectSubscriptionType')}</Label>
                      <select
                        id="subscription_type_admin"
                        name="subscription_type"
                        required
                        className={`w-full px-3 py-2 border border-input rounded-md bg-background ${language === 'ar' ? 'text-right' : ''}`}
                      >
                        <option value="Beginner">{t('beginner')}</option>
                        <option value="Advanced">{t('advanced')}</option>
                        <option value="Premium">{t('premium')}</option>
                      </select>
                    </div>

                    <div>
                      <Label htmlFor="duration_days">{t('durationDays')}</Label>
                      <Input id="duration_days" name="duration_days" type="number" required min="1" defaultValue="30" className={language === 'ar' ? 'text-right' : ''} />
                    </div>

                    <div>
                      <Label htmlFor="action_type">{t('action')}</Label>
                      <select
                        id="action_type"
                        name="action"
                        required
                        className={`w-full px-3 py-2 border border-input rounded-md bg-background ${language === 'ar' ? 'text-right' : ''}`}
                      >
                        <option value="activate">{t('activate')} - {language === 'ar' ? 'تفعيل جديد' : 'New activation'}</option>
                        <option value="extend">{t('extend')} - {language === 'ar' ? 'إضافة مدة للاشتراك الحالي' : 'Add to existing'}</option>
                        <option value="gift">{t('gift')} - {language === 'ar' ? 'هدية اشتراك' : 'Gift subscription'}</option>
                        <option value="deactivate">{t('deactivate')} - {language === 'ar' ? 'إلغاء فوري' : 'Cancel immediately'}</option>
                      </select>
                    </div>

                    <Button type="submit" className="w-full" data-testid="manage-subscription-button">
                      {t('apply')}
                    </Button>
                  </form>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>{t('allUsers')}</CardTitle>
                  <CardDescription>{t('usersList')}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3 max-h-[600px] overflow-y-auto" data-testid="users-list">
                    {users.length === 0 ? (
                      <p className="text-muted-foreground text-center py-8">{language === 'ar' ? 'لا يوجد مستخدمين' : 'No users yet'}</p>
                    ) : (
                      users.map((user) => (
                        <div key={user.user_id} className="p-4 border border-border rounded-lg space-y-2">
                          <div className="flex items-center justify-between">
                            <h3 className="font-semibold text-foreground">{user.name}</h3>
                            {user.subscription_status === 'active' ? (
                              <span className="px-2 py-1 text-xs rounded-full bg-primary/10 text-primary">{t('active')}</span>
                            ) : user.subscription_status === 'expired' ? (
                              <span className="px-2 py-1 text-xs rounded-full bg-destructive/10 text-destructive">{t('expired')}</span>
                            ) : (
                              <span className="px-2 py-1 text-xs rounded-full bg-muted text-muted-foreground">{t('none')}</span>
                            )}
                          </div>
                          <p className="text-sm text-muted-foreground">{user.email}</p>
                          {user.subscription_type && (
                            <p className="text-xs text-muted-foreground">
                              {t('subscriptionType')}: <strong>{user.subscription_type}</strong>
                            </p>
                          )}
                          {user.subscription_end_date && (
                            <p className="text-xs text-muted-foreground">
                              {t('expiresOn')}: {new Date(user.subscription_end_date).toLocaleDateString(language === 'ar' ? 'ar-SA' : 'en-US')}
                            </p>
                          )}
                        </div>
                      ))
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
