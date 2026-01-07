import { useEffect, useState, useCallback } from 'react';
import { useLanguage } from '@/contexts/LanguageContext';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { RefreshCw } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// Swiss-style professional colors
const COLORS = {
  analysisPrice: '#2C5F87', // Deep blue
  targetPrice: '#3D8B6E',   // Professional green
};

export function AnalysisPriceLineChart({ autoRefreshInterval = 60000 }) {
  const { language } = useLanguage();
  const [chartData, setChartData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [lastSync, setLastSync] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const fetchChartData = useCallback(async (showRefreshIndicator = false) => {
    if (showRefreshIndicator) setIsRefreshing(true);
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/daily-analysis/line-chart-data`, {
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        setChartData(data);
      }
    } catch (error) {
      console.error('Error fetching line chart data:', error);
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  const checkForUpdates = useCallback(async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/daily-analysis/last-sync`, {
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        if (data.last_sync && data.last_sync !== lastSync) {
          setLastSync(data.last_sync);
          // Data has been updated, refresh charts
          fetchChartData(true);
        }
      }
    } catch (error) {
      console.error('Error checking for updates:', error);
    }
  }, [lastSync, fetchChartData]);

  useEffect(() => {
    fetchChartData();
  }, [fetchChartData]);

  // Auto-refresh: poll for updates
  useEffect(() => {
    const interval = setInterval(() => {
      checkForUpdates();
    }, autoRefreshInterval);

    return () => clearInterval(interval);
  }, [checkForUpdates, autoRefreshInterval]);

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const data = payload[0]?.payload;
      return (
        <div className="bg-card border border-border p-4 rounded-lg shadow-lg min-w-[200px]">
          <p className="font-semibold text-foreground text-base mb-2">
            {data?.instrument_code}
          </p>
          <p className="text-sm text-muted-foreground mb-2">
            {language === 'ar' ? 'السوق' : 'Market'}: {data?.market}
          </p>
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <div 
                className="w-3 h-3 rounded-full" 
                style={{ backgroundColor: COLORS.analysisPrice }}
              />
              <span className="text-sm text-foreground">
                {language === 'ar' ? 'سعر التحليل' : 'Analysis Price'}: 
                <strong className="ml-1">{data?.analysis_price?.toLocaleString()}</strong>
              </span>
            </div>
            <div className="flex items-center gap-2">
              <div 
                className="w-3 h-3 rounded-full" 
                style={{ backgroundColor: COLORS.targetPrice }}
              />
              <span className="text-sm text-foreground">
                {language === 'ar' ? 'السعر المستهدف' : 'Target Price'}: 
                <strong className="ml-1">{data?.target_price?.toLocaleString()}</strong>
              </span>
            </div>
          </div>
          {data?.analysis_price && data?.target_price && (
            <div className="mt-2 pt-2 border-t border-border">
              <span className={`text-sm font-medium ${
                data.target_price > data.analysis_price 
                  ? 'text-green-600' 
                  : data.target_price < data.analysis_price 
                    ? 'text-red-600' 
                    : 'text-muted-foreground'
              }`}>
                {data.target_price > data.analysis_price 
                  ? (language === 'ar' ? '↑ صعودي' : '↑ Bullish')
                  : data.target_price < data.analysis_price 
                    ? (language === 'ar' ? '↓ هبوطي' : '↓ Bearish')
                    : (language === 'ar' ? '→ محايد' : '→ Neutral')
                }
                {' '}
                ({((data.target_price - data.analysis_price) / data.analysis_price * 100).toFixed(2)}%)
              </span>
            </div>
          )}
        </div>
      );
    }
    return null;
  };

  const CustomLegend = () => {
    return (
      <div className="flex items-center justify-center gap-6 mt-4">
        <div className="flex items-center gap-2">
          <div 
            className="w-4 h-1 rounded" 
            style={{ backgroundColor: COLORS.analysisPrice }}
          />
          <span className="text-sm text-muted-foreground">
            {language === 'ar' ? 'سعر التحليل' : 'Analysis Price'}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <div 
            className="w-4 h-1 rounded" 
            style={{ backgroundColor: COLORS.targetPrice }}
          />
          <span className="text-sm text-muted-foreground">
            {language === 'ar' ? 'السعر المستهدف' : 'Target Price'}
          </span>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>
            {language === 'ar' ? 'سعر التحليل مقابل السعر المستهدف' : 'Analysis Price vs Target Price'}
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

  if (chartData.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>
            {language === 'ar' ? 'سعر التحليل مقابل السعر المستهدف' : 'Analysis Price vs Target Price'}
          </CardTitle>
        </CardHeader>
        <CardContent className="h-[400px] flex items-center justify-center">
          <p className="text-muted-foreground">
            {language === 'ar' ? 'لا توجد بيانات للعرض' : 'No data to display'}
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between">
        <div>
          <CardTitle className="flex items-center gap-2">
            {language === 'ar' ? 'سعر التحليل مقابل السعر المستهدف' : 'Analysis Price vs Target Price'}
            {isRefreshing && (
              <RefreshCw className="w-4 h-4 animate-spin text-muted-foreground" />
            )}
          </CardTitle>
          <CardDescription>
            {language === 'ar' 
              ? 'مقارنة السعر الحالي بالسعر المستهدف لجميع الأدوات'
              : 'Compare current price vs target for all instruments'
            }
          </CardDescription>
        </div>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={400}>
          <LineChart
            data={chartData}
            margin={{
              top: 20,
              right: 30,
              left: 20,
              bottom: 60,
            }}
          >
            <CartesianGrid 
              strokeDasharray="3 3" 
              stroke="hsl(var(--border))" 
              opacity={0.5}
            />
            <XAxis 
              dataKey="instrument_code" 
              tick={{ 
                fontSize: 11, 
                fill: 'hsl(var(--muted-foreground))' 
              }}
              angle={-45}
              textAnchor="end"
              height={60}
              interval={0}
              tickLine={{ stroke: 'hsl(var(--border))' }}
              axisLine={{ stroke: 'hsl(var(--border))' }}
            />
            <YAxis 
              tick={{ 
                fontSize: 11, 
                fill: 'hsl(var(--muted-foreground))' 
              }}
              tickFormatter={(value) => value.toLocaleString()}
              tickLine={{ stroke: 'hsl(var(--border))' }}
              axisLine={{ stroke: 'hsl(var(--border))' }}
              width={80}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend content={<CustomLegend />} />
            <Line
              type="monotone"
              dataKey="analysis_price"
              name={language === 'ar' ? 'سعر التحليل' : 'Analysis Price'}
              stroke={COLORS.analysisPrice}
              strokeWidth={2}
              dot={{ 
                r: 4, 
                fill: COLORS.analysisPrice,
                strokeWidth: 2,
                stroke: '#fff'
              }}
              activeDot={{ 
                r: 6, 
                fill: COLORS.analysisPrice,
                strokeWidth: 2,
                stroke: '#fff'
              }}
            />
            <Line
              type="monotone"
              dataKey="target_price"
              name={language === 'ar' ? 'السعر المستهدف' : 'Target Price'}
              stroke={COLORS.targetPrice}
              strokeWidth={2}
              dot={{ 
                r: 4, 
                fill: COLORS.targetPrice,
                strokeWidth: 2,
                stroke: '#fff'
              }}
              activeDot={{ 
                r: 6, 
                fill: COLORS.targetPrice,
                strokeWidth: 2,
                stroke: '#fff'
              }}
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
