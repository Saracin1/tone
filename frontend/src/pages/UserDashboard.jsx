import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useLanguage } from '@/contexts/LanguageContext';
import { useSubscription } from '@/contexts/SubscriptionContext';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { LogOut, ChevronDown, ChevronLeft, Lock } from 'lucide-react';
import { LanguageSwitcher } from '@/components/LanguageSwitcher';
import { SubscriptionBanner } from '@/components/SubscriptionBanner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export default function UserDashboard() {
  const navigate = useNavigate();
  const location = useLocation();
  const { t, language } = useLanguage();
  const { subscriptionStatus, checkSubscription } = useSubscription();
  const [user, setUser] = useState(location.state?.user || null);
  const [isAuthenticated, setIsAuthenticated] = useState(location.state?.user ? true : null);
  const [markets, setMarkets] = useState([]);
  const [assets, setAssets] = useState([]);
  const [selectedAsset, setSelectedAsset] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [expandedMarkets, setExpandedMarkets] = useState({});
  const [accessDenied, setAccessDenied] = useState(false);

  useEffect(() => {
    if (location.state?.user) return;
    
    const checkAuth = async () => {
      try {
        const response = await fetch(`${BACKEND_URL}/api/auth/me`, {
          credentials: 'include'
        });
        if (!response.ok) throw new Error('Not authenticated');
        const userData = await response.json();
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

  const fetchAnalysis = async (assetId) => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/analysis/${assetId}`, {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        setAnalysis(data);
      } else {
        setAnalysis(null);
      }
    } catch (error) {
      console.error('Error fetching analysis:', error);
      setAnalysis(null);
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

  const handleAssetClick = (asset) => {
    setSelectedAsset(asset);
    fetchAnalysis(asset.asset_id);
  };

  const toggleMarket = (marketId) => {
    setExpandedMarkets(prev => ({
      ...prev,
      [marketId]: !prev[marketId]
    }));
  };

  const getAssetsByMarket = (marketId) => {
    return assets.filter(asset => asset.market_id === marketId);
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
    <div className="min-h-screen bg-background" dir={language === 'ar' ? 'rtl' : 'ltr'}>
      <header className="border-b border-border/50 bg-card/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-foreground">{t('appName')}</h1>
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

      <div className="grid grid-cols-12 gap-4 p-4 h-[calc(100vh-80px)]">
        <div className={`col-span-12 lg:col-span-2 hidden lg:flex flex-col ${language === 'ar' ? 'border-l' : 'border-r'} border-border/50 bg-card/50 backdrop-blur-sm rounded-lg overflow-hidden`}>
          <div 
            className="absolute inset-0 opacity-[0.03] pointer-events-none bg-repeat mix-blend-multiply"
            style={{ backgroundImage: "url('https://images.unsplash.com/photo-1739994885957-add0b729f051?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Nzd8MHwxfHNlYXJjaHwxfHxpc2xhbWljJTIwZ2VvbWV0cmljJTIwcGF0dGVybiUyMHNlYW1sZXNzJTIwYmVpZ2V8ZW58MHx8fHwxNzY3NDQ5MDU2fDA&ixlib=rb-4.1.0&q=85')" }}
          ></div>
          <div className="p-4 border-b border-border/50">
            <h2 className="text-lg font-semibold text-foreground">{t('markets')}</h2>
          </div>
          <ScrollArea className="flex-1 relative z-10" data-testid="markets-navigation">
            <div className="p-2 space-y-2">
              {markets.map((market) => {
                const marketAssets = getAssetsByMarket(market.market_id);
                const isExpanded = expandedMarkets[market.market_id];
                return (
                  <div key={market.market_id}>
                    <button
                      onClick={() => toggleMarket(market.market_id)}
                      className={`w-full p-3 hover:bg-accent/50 rounded-lg transition-colors flex items-center justify-between ${language === 'ar' ? 'text-right' : 'text-left'}`}
                      data-testid={`market-${market.market_id}`}
                    >
                      <span className="font-medium text-foreground">{language === 'ar' ? market.name_ar : market.name_en}</span>
                      {isExpanded ? <ChevronDown className="w-4 h-4" /> : (language === 'ar' ? <ChevronLeft className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4 rotate-180" />)}
                    </button>
                    {isExpanded && (
                      <div className={`space-y-1 ${language === 'ar' ? 'mr-4' : 'ml-4'}`}>
                        {marketAssets.length === 0 ? (
                          <p className="text-xs text-muted-foreground p-2">{t('noAssets')}</p>
                        ) : (
                          marketAssets.map((asset) => (
                            <button
                              key={asset.asset_id}
                              onClick={() => handleAssetClick(asset)}
                              className={`w-full p-2 rounded-lg transition-colors text-sm ${language === 'ar' ? 'text-right' : 'text-left'} ${
                                selectedAsset?.asset_id === asset.asset_id
                                  ? 'bg-primary text-primary-foreground'
                                  : 'hover:bg-accent/50 text-muted-foreground'
                              }`}
                              data-testid={`asset-${asset.asset_id}`}
                            >
                              {language === 'ar' ? asset.name_ar : asset.name_en}
                            </button>
                          ))
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </ScrollArea>
        </div>

        <div className="col-span-12 lg:col-span-7 flex flex-col bg-card rounded-lg shadow-sm border border-border/50 overflow-hidden" data-testid="analysis-display">
          <div className="flex-1 p-6 overflow-y-auto">
            {!selectedAsset ? (
              <div className="h-full flex items-center justify-center">
                <div className="text-center">
                  <div className="w-24 h-24 mx-auto mb-4 bg-secondary/20 rounded-full flex items-center justify-center">
                    <svg className="w-12 h-12 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                  </div>
                  <h2 className="text-2xl font-bold text-foreground mb-2">{t('welcome')}</h2>
                  <p className="text-muted-foreground">{t('selectAssetToView')}</p>
                </div>
              </div>
            ) : !analysis ? (
              <div className="h-full flex items-center justify-center">
                <div className="text-center">
                  <h2 className="text-xl font-bold text-foreground mb-2">{language === 'ar' ? selectedAsset.name_ar : selectedAsset.name_en}</h2>
                  <p className="text-muted-foreground">{t('noAnalysis')}</p>
                </div>
              </div>
            ) : (
              <div className="space-y-6">
                <div>
                  <h1 className="text-4xl font-bold text-foreground mb-2">{language === 'ar' ? selectedAsset.name_ar : selectedAsset.name_en}</h1>
                  <p className="text-lg text-muted-foreground">{language === 'ar' ? selectedAsset.name_en : selectedAsset.name_ar}</p>
                </div>

                <Card className="p-6 bg-gradient-to-br from-primary/10 to-secondary/10 border-primary/20">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground mb-1">{t('direction')}</p>
                      <p className="text-3xl font-bold text-primary">{analysis.bias}</p>
                    </div>
                    <div className={language === 'ar' ? 'text-left' : 'text-right'}>
                      <p className="text-sm text-muted-foreground mb-1">{t('confidence')}</p>
                      <p className="text-xl font-semibold text-foreground">{analysis.confidence_level}</p>
                    </div>
                  </div>
                </Card>

                <div>
                  <h2 className="text-2xl font-semibold text-foreground mb-3">{t('keyLevelsTitle')}</h2>
                  <Card className="p-6">
                    <p className="text-lg text-foreground whitespace-pre-wrap leading-relaxed">{analysis.key_levels}</p>
                  </Card>
                </div>

                <div>
                  <h2 className="text-2xl font-semibold text-foreground mb-3">{t('scenarioTitle')}</h2>
                  <Card className="p-6">
                    <p className="text-base text-foreground whitespace-pre-wrap leading-relaxed">{analysis.scenario_text}</p>
                  </Card>
                </div>

                <div className={`text-xs text-muted-foreground ${language === 'ar' ? 'text-left' : 'text-right'}`}>
                  {t('lastUpdated')}: {new Date(analysis.updated_at).toLocaleString(language === 'ar' ? 'ar-SA' : 'en-US')}
                </div>
              </div>
            )}
          </div>
        </div>

        <div className={`col-span-3 hidden lg:flex flex-col ${language === 'ar' ? 'border-r' : 'border-l'} border-border/50 bg-card/50 backdrop-blur-sm rounded-lg overflow-hidden`}>
          <div 
            className="absolute inset-0 opacity-[0.03] pointer-events-none bg-repeat mix-blend-multiply"
            style={{ backgroundImage: "url('https://images.unsplash.com/photo-1739994885957-add0b729f051?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Nzd8MHwxfHNlYXJjaHwxfHxpc2xhbWljJTIwZ2VvbWV0cmljJTIwcGF0dGVybiUyMHNlYW1sZXNzJTIwYmVpZ2V8ZW58MHx8fHwxNzY3NDQ5MDU2fDA&ixlib=rb-4.1.0&q=85')" }}
          ></div>
          <div className="p-4 border-b border-border/50">
            <h2 className="text-lg font-semibold text-foreground">{t('additionalInsights')}</h2>
          </div>
          <ScrollArea className="flex-1 relative z-10" data-testid="insights-panel">
            {analysis && (
              <div className="p-4 space-y-4">
                {analysis.insight_text && (
                  <Card className="p-4">
                    <h3 className="font-semibold text-foreground mb-2">{t('higherTimeframe')}</h3>
                    <p className="text-sm text-muted-foreground whitespace-pre-wrap leading-relaxed">{analysis.insight_text}</p>
                  </Card>
                )}
                {analysis.risk_note && (
                  <Card className="p-4 bg-destructive/10 border-destructive/20">
                    <h3 className="font-semibold text-destructive mb-2">{t('riskWarning')}</h3>
                    <p className="text-sm text-foreground whitespace-pre-wrap leading-relaxed">{analysis.risk_note}</p>
                  </Card>
                )}
                {!analysis.insight_text && !analysis.risk_note && (
                  <p className="text-sm text-muted-foreground text-center py-8">{t('noInsights')}</p>
                )}
              </div>
            )}
          </ScrollArea>
        </div>
      </div>
    </div>
  );
}
