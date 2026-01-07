import { useEffect, useState, useCallback } from 'react';
import { useLanguage } from '@/contexts/LanguageContext';
import { 
  BarChart, 
  Bar, 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer,
  Cell,
  ReferenceLine
} from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { 
  TrendingUp, 
  TrendingDown, 
  Target, 
  Award, 
  BarChart3, 
  LineChartIcon,
  Trophy,
  Activity,
  Percent,
  Calendar
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// Swiss-style professional colors
const COLORS = {
  profit: '#16A34A',    // Green
  loss: '#DC2626',      // Red
  neutral: '#6B7280',   // Gray
  primary: '#2C5F87',   // Deep blue
  cumulative: '#3D8B6E', // Professional green
};

export function HistoryOfSuccess({ autoRefreshInterval = 60000 }) {
  const { language } = useLanguage();
  const [summary, setSummary] = useState(null);
  const [performanceData, setPerformanceData] = useState([]);
  const [cumulativeData, setCumulativeData] = useState([]);
  const [forecasts, setForecasts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  const fetchData = useCallback(async () => {
    try {
      const [summaryRes, performanceRes, cumulativeRes, forecastsRes] = await Promise.all([
        fetch(`${BACKEND_URL}/api/history/summary`, { credentials: 'include' }),
        fetch(`${BACKEND_URL}/api/history/performance`, { credentials: 'include' }),
        fetch(`${BACKEND_URL}/api/history/cumulative`, { credentials: 'include' }),
        fetch(`${BACKEND_URL}/api/history/forecasts?limit=50`, { credentials: 'include' })
      ]);

      if (summaryRes.ok) setSummary(await summaryRes.json());
      if (performanceRes.ok) setPerformanceData(await performanceRes.json());
      if (cumulativeRes.ok) setCumulativeData(await cumulativeRes.json());
      if (forecastsRes.ok) setForecasts(await forecastsRes.json());
    } catch (error) {
      console.error('Error fetching history data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, autoRefreshInterval);
    return () => clearInterval(interval);
  }, [fetchData, autoRefreshInterval]);

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    try {
      return new Date(dateStr).toLocaleDateString(language === 'ar' ? 'ar-SA' : 'en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    } catch {
      return dateStr;
    }
  };

  const PerformanceBarTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-card border border-border p-4 rounded-lg shadow-lg">
          <p className="font-semibold text-foreground">{data.instrument_code}</p>
          <p className="text-sm text-muted-foreground">{data.market}</p>
          <div className="mt-2 space-y-1 text-sm">
            <p>{language === 'ar' ? 'إجمالي العائد' : 'Total Return'}: 
              <span className={`font-bold ml-1 ${data.total_pl_percent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {data.total_pl_percent >= 0 ? '+' : ''}{data.total_pl_percent}%
              </span>
            </p>
            <p>{language === 'ar' ? 'نسبة النجاح' : 'Win Rate'}: 
              <span className="font-bold ml-1">{data.win_rate?.toFixed(1)}%</span>
            </p>
            <p>{language === 'ar' ? 'التوقعات' : 'Forecasts'}: 
              <span className="font-bold ml-1">{data.successful_forecasts}/{data.total_forecasts}</span>
            </p>
          </div>
        </div>
      );
    }
    return null;
  };

  const CumulativeTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-card border border-border p-4 rounded-lg shadow-lg">
          <p className="font-semibold text-foreground">{formatDate(data.date)}</p>
          <p className="text-sm text-muted-foreground">{data.instrument} ({data.market})</p>
          <div className="mt-2 space-y-1 text-sm">
            <p>{language === 'ar' ? 'العائد' : 'Return'}: 
              <span className={`font-bold ml-1 ${data.pl_percent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {data.pl_percent >= 0 ? '+' : ''}{data.pl_percent}%
              </span>
            </p>
            <p>{language === 'ar' ? 'العائد التراكمي' : 'Cumulative'}: 
              <span className={`font-bold ml-1 ${data.cumulative_return >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {data.cumulative_return >= 0 ? '+' : ''}{data.cumulative_return}%
              </span>
            </p>
            <p>{language === 'ar' ? 'نسبة النجاح' : 'Win Rate'}: 
              <span className="font-bold ml-1">{data.win_rate}%</span>
            </p>
          </div>
        </div>
      );
    }
    return null;
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Trophy className="w-5 h-5 text-yellow-500" />
            {language === 'ar' ? 'سجل النجاح' : 'History of Success'}
          </CardTitle>
        </CardHeader>
        <CardContent className="h-[400px] flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
            <p className="mt-2 text-sm text-muted-foreground">
              {language === 'ar' ? 'جاري التحميل...' : 'Loading...'}
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!summary || summary.total_forecasts === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Trophy className="w-5 h-5 text-yellow-500" />
            {language === 'ar' ? 'سجل النجاح' : 'History of Success'}
          </CardTitle>
        </CardHeader>
        <CardContent className="h-[400px] flex items-center justify-center">
          <div className="text-center">
            <Trophy className="w-16 h-16 mx-auto mb-4 text-muted-foreground/30" />
            <p className="text-muted-foreground">
              {language === 'ar' ? 'لا توجد توقعات مسجلة بعد' : 'No forecast history available yet'}
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Summary Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-br from-primary/10 to-primary/5">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">
                  {language === 'ar' ? 'إجمالي التوقعات' : 'Total Forecasts'}
                </p>
                <p className="text-2xl font-bold text-foreground">{summary.total_forecasts}</p>
              </div>
              <Target className="w-8 h-8 text-primary/50" />
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-green-500/10 to-green-500/5">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">
                  {language === 'ar' ? 'نسبة النجاح' : 'Win Rate'}
                </p>
                <p className="text-2xl font-bold text-green-600">{summary.win_rate}%</p>
              </div>
              <Award className="w-8 h-8 text-green-500/50" />
            </div>
          </CardContent>
        </Card>
        
        <Card className={`bg-gradient-to-br ${summary.total_return_percent >= 0 ? 'from-green-500/10 to-green-500/5' : 'from-red-500/10 to-red-500/5'}`}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">
                  {language === 'ar' ? 'العائد الإجمالي' : 'Total Return'}
                </p>
                <p className={`text-2xl font-bold ${summary.total_return_percent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {summary.total_return_percent >= 0 ? '+' : ''}{summary.total_return_percent}%
                </p>
              </div>
              {summary.total_return_percent >= 0 
                ? <TrendingUp className="w-8 h-8 text-green-500/50" />
                : <TrendingDown className="w-8 h-8 text-red-500/50" />
              }
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-blue-500/10 to-blue-500/5">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">
                  {language === 'ar' ? 'متوسط العائد' : 'Avg Return'}
                </p>
                <p className={`text-2xl font-bold ${summary.avg_return_percent >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {summary.avg_return_percent >= 0 ? '+' : ''}{summary.avg_return_percent}%
                </p>
              </div>
              <Percent className="w-8 h-8 text-blue-500/50" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Trophy className="w-5 h-5 text-yellow-500" />
            {language === 'ar' ? 'سجل النجاح' : 'History of Success'}
          </CardTitle>
          <CardDescription>
            {language === 'ar' 
              ? 'أداء التوقعات السابقة والعائد التراكمي'
              : 'Past forecast performance and cumulative returns'
            }
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="grid w-full grid-cols-3 max-w-lg mx-auto mb-6">
              <TabsTrigger value="overview" className="flex items-center gap-2">
                <Activity className="w-4 h-4" />
                {language === 'ar' ? 'نظرة عامة' : 'Overview'}
              </TabsTrigger>
              <TabsTrigger value="performance" className="flex items-center gap-2">
                <BarChart3 className="w-4 h-4" />
                {language === 'ar' ? 'الأداء' : 'Performance'}
              </TabsTrigger>
              <TabsTrigger value="history" className="flex items-center gap-2">
                <Calendar className="w-4 h-4" />
                {language === 'ar' ? 'السجل' : 'History'}
              </TabsTrigger>
            </TabsList>

            {/* Overview Tab - Cumulative Line Chart */}
            <TabsContent value="overview" className="mt-0">
              {cumulativeData.length > 0 ? (
                <ResponsiveContainer width="100%" height={400}>
                  <LineChart data={cumulativeData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.5} />
                    <XAxis 
                      dataKey="date" 
                      tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }}
                      tickFormatter={(value) => formatDate(value)}
                      angle={-45}
                      textAnchor="end"
                      height={60}
                    />
                    <YAxis 
                      tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }}
                      tickFormatter={(value) => `${value}%`}
                    />
                    <Tooltip content={<CumulativeTooltip />} />
                    <ReferenceLine y={0} stroke="hsl(var(--border))" strokeDasharray="3 3" />
                    <Line
                      type="monotone"
                      dataKey="cumulative_return"
                      name={language === 'ar' ? 'العائد التراكمي' : 'Cumulative Return'}
                      stroke={COLORS.cumulative}
                      strokeWidth={3}
                      dot={{ r: 4, fill: COLORS.cumulative, strokeWidth: 2, stroke: '#fff' }}
                      activeDot={{ r: 6, fill: COLORS.cumulative, strokeWidth: 2, stroke: '#fff' }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[400px] flex items-center justify-center">
                  <p className="text-muted-foreground">
                    {language === 'ar' ? 'لا توجد بيانات تراكمية بعد' : 'No cumulative data available yet'}
                  </p>
                </div>
              )}
            </TabsContent>

            {/* Performance Tab - Bar Chart */}
            <TabsContent value="performance" className="mt-0">
              {performanceData.length > 0 ? (
                <ResponsiveContainer width="100%" height={400}>
                  <BarChart data={performanceData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.5} />
                    <XAxis 
                      dataKey="instrument_code" 
                      tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }}
                      angle={-45}
                      textAnchor="end"
                      height={60}
                      interval={0}
                    />
                    <YAxis 
                      tick={{ fontSize: 11, fill: 'hsl(var(--muted-foreground))' }}
                      tickFormatter={(value) => `${value}%`}
                    />
                    <Tooltip content={<PerformanceBarTooltip />} />
                    <ReferenceLine y={0} stroke="hsl(var(--border))" strokeDasharray="3 3" />
                    <Bar dataKey="total_pl_percent" name={language === 'ar' ? 'العائد' : 'Return'} radius={[4, 4, 0, 0]}>
                      {performanceData.map((entry, index) => (
                        <Cell 
                          key={`cell-${index}`} 
                          fill={entry.total_pl_percent >= 0 ? COLORS.profit : COLORS.loss} 
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[400px] flex items-center justify-center">
                  <p className="text-muted-foreground">
                    {language === 'ar' ? 'لا توجد بيانات أداء بعد' : 'No performance data available yet'}
                  </p>
                </div>
              )}
            </TabsContent>

            {/* History Tab - Table */}
            <TabsContent value="history" className="mt-0">
              <div className="overflow-x-auto max-h-[400px] overflow-y-auto">
                <table className="w-full text-sm">
                  <thead className="sticky top-0 bg-card border-b">
                    <tr className="text-muted-foreground">
                      <th className="text-left p-3">{language === 'ar' ? 'الأداة' : 'Instrument'}</th>
                      <th className="text-left p-3">{language === 'ar' ? 'السوق' : 'Market'}</th>
                      <th className="text-left p-3">{language === 'ar' ? 'التاريخ' : 'Date'}</th>
                      <th className="text-left p-3">{language === 'ar' ? 'الاتجاه' : 'Direction'}</th>
                      <th className="text-right p-3">{language === 'ar' ? 'سعر الدخول' : 'Entry'}</th>
                      <th className="text-right p-3">{language === 'ar' ? 'الهدف' : 'Target'}</th>
                      <th className="text-right p-3">{language === 'ar' ? 'النتيجة' : 'Result'}</th>
                      <th className="text-right p-3">{language === 'ar' ? 'العائد' : 'P/L'}</th>
                      <th className="text-center p-3">{language === 'ar' ? 'الحالة' : 'Status'}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {forecasts.map((forecast, idx) => (
                      <tr key={forecast.record_id || idx} className="border-b border-border/50 hover:bg-accent/30">
                        <td className="p-3 font-medium">{forecast.instrument_code}</td>
                        <td className="p-3 text-muted-foreground">{forecast.market}</td>
                        <td className="p-3 text-muted-foreground">{formatDate(forecast.forecast_date)}</td>
                        <td className="p-3">
                          <span className={`flex items-center gap-1 ${forecast.forecast_direction === 'Bullish' ? 'text-green-600' : 'text-red-600'}`}>
                            {forecast.forecast_direction === 'Bullish' 
                              ? <TrendingUp className="w-4 h-4" />
                              : <TrendingDown className="w-4 h-4" />
                            }
                            {forecast.forecast_direction}
                          </span>
                        </td>
                        <td className="p-3 text-right font-mono">{forecast.entry_price?.toLocaleString()}</td>
                        <td className="p-3 text-right font-mono">{forecast.forecast_target_price?.toLocaleString()}</td>
                        <td className="p-3 text-right font-mono">
                          {forecast.actual_result_price?.toLocaleString() || '-'}
                        </td>
                        <td className={`p-3 text-right font-mono font-bold ${
                          forecast.calculated_pl_percent === null ? 'text-muted-foreground' :
                          forecast.calculated_pl_percent >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {forecast.calculated_pl_percent !== null 
                            ? `${forecast.calculated_pl_percent >= 0 ? '+' : ''}${forecast.calculated_pl_percent}%`
                            : '-'
                          }
                        </td>
                        <td className="p-3 text-center">
                          <Badge variant={
                            forecast.status === 'success' ? 'success' :
                            forecast.status === 'failed' ? 'destructive' : 'secondary'
                          } className={
                            forecast.status === 'success' ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' :
                            forecast.status === 'failed' ? 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400' :
                            'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400'
                          }>
                            {forecast.status === 'success' 
                              ? (language === 'ar' ? 'ناجح' : 'Success')
                              : forecast.status === 'failed'
                                ? (language === 'ar' ? 'فاشل' : 'Failed')
                                : (language === 'ar' ? 'قيد الانتظار' : 'Pending')
                            }
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}
