import { useEffect, useState } from 'react';
import { useLanguage } from '@/contexts/LanguageContext';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// Swiss-style professional colors (muted, private banking aesthetic)
const PINE_COLORS = [
  '#2C5F87', // Deep blue
  '#5A7D9A', // Steel blue
  '#8B9DAE', // Cool gray-blue
  '#A4B3BF', // Light steel
  '#6B8A9D', // Slate blue
  '#4A6B82', // Dark slate
  '#7FA5BD', // Soft blue
  '#3D5A6C', // Charcoal blue
  '#91A7B7', // Silver blue
  '#5E7A8E', // Shadow blue
  '#788FA3', // Stone blue
  '#4D6A7D', // Deep teal
];

export function AnalysisPriceChart() {
  const { t, language } = useLanguage();
  const [chartData, setChartData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    fetchChartData();
  }, []);

  const fetchChartData = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/daily-analysis/chart-data`, {
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        
        // Calculate total
        const totalValue = data.reduce((sum, item) => sum + item.value, 0);
        setTotal(totalValue);
        
        // Prepare chart data with percentages
        const chartData = data.map((item, index) => ({
          name: item.instrument,
          value: item.value,
          market: item.market,
          percentage: ((item.value / totalValue) * 100).toFixed(2),
          fill: PINE_COLORS[index % PINE_COLORS.length]
        }));
        
        // Sort by value descending
        chartData.sort((a, b) => b.value - a.value);
        
        setChartData(chartData);
      }
    } catch (error) {
      console.error('Error fetching chart data:', error);
    } finally {
      setLoading(false);
    }
  };

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-card border border-border p-3 rounded-lg shadow-lg">
          <p className="font-semibold text-foreground">{data.name}</p>
          <p className="text-sm text-muted-foreground">{data.market}</p>
          <p className="text-sm text-foreground mt-1">
            {language === 'ar' ? 'السعر' : 'Price'}: <strong>{data.value.toLocaleString()}</strong>
          </p>
          <p className="text-sm text-primary font-semibold">
            {data.percentage}%
          </p>
        </div>
      );
    }
    return null;
  };

  const CustomLegend = ({ payload }) => {
    return (
      <div className="grid grid-cols-2 gap-2 mt-4 text-xs">
        {payload.map((entry, index) => (
          <div key={index} className="flex items-center gap-2">
            <div 
              className="w-3 h-3 rounded-sm" 
              style={{ backgroundColor: entry.color }}
            />
            <span className="text-muted-foreground truncate">
              {entry.value} ({entry.payload.percentage}%)
            </span>
          </div>
        ))}
      </div>
    );
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{language === 'ar' ? 'توزيع أسعار التحليل' : 'Analysis Price Distribution'}</CardTitle>
        </CardHeader>
        <CardContent className="h-[400px] flex items-center justify-center">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
            <p className="mt-2 text-sm text-muted-foreground">{t('loading')}</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (chartData.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{language === 'ar' ? 'توزيع أسعار التحليل' : 'Analysis Price Distribution'}</CardTitle>
        </CardHeader>
        <CardContent className="h-[400px] flex items-center justify-center">
          <p className="text-muted-foreground">{language === 'ar' ? 'لا توجد بيانات للعرض' : 'No data to display'}</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>{language === 'ar' ? 'توزيع أسعار التحليل' : 'Analysis Price Distribution'}</CardTitle>
        <CardDescription>
          {language === 'ar' 
            ? `الوزن النسبي لكل أداة من إجمالي ${total.toLocaleString()}`
            : `Relative weight of each instrument out of total ${total.toLocaleString()}`
          }
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={400}>
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="45%"
              labelLine={false}
              label={({ name, percentage }) => `${name} (${percentage}%)`}
              outerRadius={120}
              innerRadius={60}
              fill="#8884d8"
              dataKey="value"
              strokeWidth={2}
              stroke="#ffffff"
            >
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.fill} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
            <Legend content={<CustomLegend />} />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
