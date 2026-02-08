import { useEffect, useState } from 'react';
import { TrendingDown, BarChart3, Brain, Zap } from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  AreaChart,
  BarChart,
  Bar,
  ReferenceLine,
} from 'recharts';
import { trainingService } from '@/services/training.service';
import type { ForgettingCurveResponse } from '@/types';
import { toast } from 'sonner';
import { useLanguage } from '@/contexts/LanguageContext';

export default function ForgettingCurvePage() {
  const { t } = useLanguage();
  const [data, setData] = useState<ForgettingCurveResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function loadData() {
      try {
        const resp = await trainingService.getForgettingCurve();
        if (!cancelled) setData(resp);
      } catch {
        if (!cancelled) toast.error(t.forgettingCurve.errors.loadFailed);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    loadData();
    return () => { cancelled = true; };
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (!data || data.points.length === 0) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="flex items-center gap-3 mb-6">
          <TrendingDown className="h-7 w-7 text-blue-600" />
          <h1 className="text-2xl font-bold">{t.forgettingCurve.title}</h1>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl border p-12 text-center">
          <Brain className="h-16 w-16 text-gray-300 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-600 dark:text-gray-400 mb-2">
            {t.forgettingCurve.emptyState.noData}
          </h2>
          <p className="text-gray-500 dark:text-gray-500">
            {t.forgettingCurve.emptyState.startTraining}
            <br />
            {t.forgettingCurve.emptyState.needCards}
          </p>
        </div>
      </div>
    );
  }

  // Объединяем реальные точки и теоретическую кривую для графика
  const chartData = data.theoretical_curve.map((t) => {
    const realPoint = data.points.find(
      (p) => Math.abs(p.interval_days - t.day) <= t.day * 0.4,
    );
    return {
      day: t.day,
      theoretical: t.retention,
      actual: realPoint?.retention_rate ?? null,
      label: realPoint?.label ?? `${t.day}д`,
      cards: realPoint?.total_cards ?? 0,
    };
  });

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <TrendingDown className="h-7 w-7 text-blue-600" />
        <h1 className="text-2xl font-bold">{t.forgettingCurve.title}</h1>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-xl border p-4 text-center">
          <BarChart3 className="h-6 w-6 text-blue-500 mx-auto mb-2" />
          <div className="text-2xl font-bold">{data.summary.total_reviews}</div>
          <div className="text-xs text-gray-500">{t.forgettingCurve.summary.cardsReviewed}</div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl border p-4 text-center">
          <Brain className="h-6 w-6 text-green-500 mx-auto mb-2" />
          <div className="text-2xl font-bold">{data.summary.avg_retention}%</div>
          <div className="text-xs text-gray-500">{t.forgettingCurve.summary.avgRetention}</div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl border p-4 text-center">
          <Zap className="h-6 w-6 text-orange-500 mx-auto mb-2" />
          <div className="text-2xl font-bold">{data.summary.current_stability}д</div>
          <div className="text-xs text-gray-500">{t.forgettingCurve.summary.avgStability}</div>
        </div>
      </div>

      {/* Main Chart: Forgetting Curve */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border p-5">
        <h2 className="text-lg font-semibold mb-4">
          {t.forgettingCurve.chart.title}
        </h2>
        <p className="text-sm text-gray-500 mb-4">
          {t.forgettingCurve.chart.description}
        </p>
        <ResponsiveContainer width="100%" height={350}>
          <AreaChart data={chartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
            <XAxis
              dataKey="day"
              label={{ value: t.forgettingCurve.chart.days, position: 'insideBottom', offset: -5 }}
              tickFormatter={(v) => `${v}д`}
            />
            <YAxis
              domain={[0, 100]}
              label={{
                value: t.forgettingCurve.chart.retention,
                angle: -90,
                position: 'insideLeft',
              }}
              tickFormatter={(v) => `${v}%`}
            />
            <Tooltip
              formatter={(value: number, name: string) => [
                `${value?.toFixed(1)}%`,
                name === 'theoretical' ? t.forgettingCurve.chart.theoretical : t.forgettingCurve.chart.yourData,
              ]}
              labelFormatter={(v) => `${t.forgettingCurve.table.interval}: ${v} ${t.forgettingCurve.table.days}`}
            />
            <Legend
              formatter={(value) =>
                value === 'theoretical' ? t.forgettingCurve.chart.theoreticalCurve : t.forgettingCurve.chart.yourData
              }
            />
            <ReferenceLine y={90} stroke="#22c55e" strokeDasharray="4 4" label={t.forgettingCurve.chart.goal90} />
            <Area
              type="monotone"
              dataKey="theoretical"
              stroke="#3b82f6"
              fill="#3b82f6"
              fillOpacity={0.1}
              strokeWidth={2}
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="actual"
              stroke="#ef4444"
              strokeWidth={3}
              dot={{ r: 6, fill: '#ef4444', strokeWidth: 2, stroke: '#fff' }}
              connectNulls={false}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Bar Chart: Cards per Interval */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border p-5">
        <h2 className="text-lg font-semibold mb-4">
          {t.forgettingCurve.barChart.title}
        </h2>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={data.points} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
            <XAxis dataKey="label" />
            <YAxis />
            <Tooltip
              formatter={(value: number, name: string) => [
                value,
                name === 'total_cards'
                  ? t.forgettingCurve.barChart.totalCards
                  : name === 'successful'
                    ? t.forgettingCurve.barChart.successful
                    : name,
              ]}
            />
            <Legend
              formatter={(value) =>
                value === 'total_cards'
                  ? t.forgettingCurve.barChart.totalCards
                  : value === 'successful'
                    ? t.forgettingCurve.barChart.successful
                    : value
              }
            />
            <Bar dataKey="total_cards" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            <Bar dataKey="successful" fill="#22c55e" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Detailed Table */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 dark:bg-gray-700">
            <tr>
              <th className="px-4 py-3 text-left font-medium">{t.forgettingCurve.table.interval}</th>
              <th className="px-4 py-3 text-center font-medium">{t.forgettingCurve.table.cards}</th>
              <th className="px-4 py-3 text-center font-medium">{t.forgettingCurve.table.successful}</th>
              <th className="px-4 py-3 text-center font-medium">{t.forgettingCurve.table.retention}</th>
            </tr>
          </thead>
          <tbody>
            {data.points.map((p, i) => (
              <tr
                key={i}
                className="border-t border-gray-100 dark:border-gray-700"
              >
                <td className="px-4 py-3 font-medium">{p.label} {t.forgettingCurve.table.days}</td>
                <td className="px-4 py-3 text-center">{p.total_cards}</td>
                <td className="px-4 py-3 text-center text-green-600">
                  {p.successful}
                </td>
                <td className="px-4 py-3 text-center">
                  <span
                    className={`inline-flex px-2 py-0.5 rounded-full text-xs font-semibold ${
                      p.retention_rate >= 90
                        ? 'bg-green-100 text-green-800'
                        : p.retention_rate >= 70
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-red-100 text-red-800'
                    }`}
                  >
                    {p.retention_rate}%
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
