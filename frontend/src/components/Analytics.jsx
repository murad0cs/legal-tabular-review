import { useMemo } from 'react';
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, Legend
} from 'recharts';
import { TrendingUp, AlertTriangle, CheckCircle, Clock, XCircle } from 'lucide-react';
import clsx from 'clsx';

const STATUS_COLORS = {
  approved: '#10b981',
  pending: '#f59e0b',
  rejected: '#ef4444',
  edited: '#8b5cf6',
};

const CONFIDENCE_COLORS = {
  high: '#10b981',
  medium: '#f59e0b',
  low: '#ef4444',
};

/**
 * Analytics panel showing extraction statistics and insights.
 */
function Analytics({ values, fields, documents }) {
  const stats = useMemo(() => {
    if (!values.length) return null;

    // Status distribution
    const statusCounts = values.reduce((acc, v) => {
      acc[v.status] = (acc[v.status] || 0) + 1;
      return acc;
    }, {});

    const statusData = Object.entries(statusCounts).map(([name, value]) => ({
      name: name.charAt(0).toUpperCase() + name.slice(1),
      value,
      color: STATUS_COLORS[name] || '#64748b',
    }));

    // Confidence distribution
    const confidenceBuckets = { high: 0, medium: 0, low: 0 };
    values.forEach(v => {
      const conf = v.confidence || 0;
      if (conf >= 0.8) confidenceBuckets.high++;
      else if (conf >= 0.5) confidenceBuckets.medium++;
      else confidenceBuckets.low++;
    });

    const confidenceData = [
      { name: 'High (≥80%)', value: confidenceBuckets.high, color: CONFIDENCE_COLORS.high },
      { name: 'Medium (50-79%)', value: confidenceBuckets.medium, color: CONFIDENCE_COLORS.medium },
      { name: 'Low (<50%)', value: confidenceBuckets.low, color: CONFIDENCE_COLORS.low },
    ];

    // Per-field average confidence
    const fieldConfidence = {};
    values.forEach(v => {
      if (!fieldConfidence[v.template_field_id]) {
        fieldConfidence[v.template_field_id] = { sum: 0, count: 0 };
      }
      fieldConfidence[v.template_field_id].sum += v.confidence || 0;
      fieldConfidence[v.template_field_id].count++;
    });

    const fieldData = fields
      .map(f => ({
        name: f.field_label.length > 15 ? f.field_label.slice(0, 15) + '...' : f.field_label,
        fullName: f.field_label,
        confidence: fieldConfidence[f.id]
          ? Math.round((fieldConfidence[f.id].sum / fieldConfidence[f.id].count) * 100)
          : 0,
      }))
      .sort((a, b) => a.confidence - b.confidence);

    // Low confidence values (for attention)
    const lowConfidenceValues = values
      .filter(v => (v.confidence || 0) < 0.5)
      .slice(0, 5);

    // Overall stats
    const avgConfidence = values.reduce((sum, v) => sum + (v.confidence || 0), 0) / values.length;
    const completionRate = (statusCounts.approved || 0) / values.length;

    return {
      statusData,
      confidenceData,
      fieldData,
      lowConfidenceValues,
      avgConfidence,
      completionRate,
      total: values.length,
      approved: statusCounts.approved || 0,
      pending: statusCounts.pending || 0,
      rejected: statusCounts.rejected || 0,
    };
  }, [values, fields]);

  if (!stats) {
    return (
      <div className="glass rounded-2xl p-6 text-center text-slate-400">
        No extraction data available for analytics.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-4 gap-4">
        <SummaryCard
          icon={TrendingUp}
          label="Avg Confidence"
          value={`${Math.round(stats.avgConfidence * 100)}%`}
          color={stats.avgConfidence >= 0.7 ? 'emerald' : stats.avgConfidence >= 0.5 ? 'amber' : 'red'}
        />
        <SummaryCard
          icon={CheckCircle}
          label="Approved"
          value={stats.approved}
          subtitle={`of ${stats.total}`}
          color="emerald"
        />
        <SummaryCard
          icon={Clock}
          label="Pending Review"
          value={stats.pending}
          color="amber"
        />
        <SummaryCard
          icon={XCircle}
          label="Rejected"
          value={stats.rejected}
          color="red"
        />
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* Status Distribution */}
        <div className="glass rounded-2xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Status Distribution</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={stats.statusData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {stats.statusData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1e293b',
                    border: '1px solid #475569',
                    borderRadius: '8px',
                  }}
                  labelStyle={{ color: '#f1f5f9' }}
                />
                <Legend
                  formatter={(value) => <span className="text-slate-300">{value}</span>}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Confidence Distribution */}
        <div className="glass rounded-2xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Confidence Levels</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={stats.confidenceData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {stats.confidenceData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1e293b',
                    border: '1px solid #475569',
                    borderRadius: '8px',
                  }}
                />
                <Legend
                  formatter={(value) => <span className="text-slate-300">{value}</span>}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Field Confidence Bar Chart */}
      <div className="glass rounded-2xl p-6">
        <h3 className="text-lg font-semibold text-white mb-4">Confidence by Field</h3>
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={stats.fieldData} layout="vertical" margin={{ left: 20 }}>
              <XAxis type="number" domain={[0, 100]} tick={{ fill: '#94a3b8' }} />
              <YAxis
                type="category"
                dataKey="name"
                width={120}
                tick={{ fill: '#94a3b8', fontSize: 12 }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e293b',
                  border: '1px solid #475569',
                  borderRadius: '8px',
                }}
                formatter={(value) => [`${value}%`, 'Confidence']}
                labelFormatter={(label, payload) => payload?.[0]?.payload?.fullName || label}
              />
              <Bar
                dataKey="confidence"
                radius={[0, 4, 4, 0]}
                fill="#6366f1"
              >
                {stats.fieldData.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={
                      entry.confidence >= 80
                        ? CONFIDENCE_COLORS.high
                        : entry.confidence >= 50
                        ? CONFIDENCE_COLORS.medium
                        : CONFIDENCE_COLORS.low
                    }
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Low Confidence Alert */}
      {stats.lowConfidenceValues.length > 0 && (
        <div className="glass rounded-2xl p-6 border border-amber-500/30">
          <div className="flex items-center gap-3 mb-4">
            <AlertTriangle className="w-5 h-5 text-amber-400" />
            <h3 className="text-lg font-semibold text-white">Needs Attention</h3>
          </div>
          <p className="text-slate-400 mb-4">
            {stats.lowConfidenceValues.length} value(s) with low confidence (&lt;50%) may need manual review.
          </p>
          <div className="space-y-2">
            {stats.lowConfidenceValues.map(v => (
              <div
                key={v.id}
                className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg"
              >
                <div>
                  <span className="text-white">{v.field_label || 'Unknown Field'}</span>
                  <span className="text-slate-500 mx-2">•</span>
                  <span className="text-slate-400">{v.raw_value || 'No value'}</span>
                </div>
                <span className="text-red-400 text-sm font-medium">
                  {Math.round((v.confidence || 0) * 100)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function SummaryCard({ icon: Icon, label, value, subtitle, color }) {
  const colorClasses = {
    emerald: 'bg-emerald-500/20 text-emerald-400',
    amber: 'bg-amber-500/20 text-amber-400',
    red: 'bg-red-500/20 text-red-400',
    blue: 'bg-blue-500/20 text-blue-400',
  };

  return (
    <div className="glass rounded-xl p-4 flex items-center gap-4">
      <div className={clsx('w-12 h-12 rounded-lg flex items-center justify-center', colorClasses[color])}>
        <Icon className="w-6 h-6" />
      </div>
      <div>
        <p className="text-sm text-slate-400">{label}</p>
        <p className="text-2xl font-bold text-white">
          {value}
          {subtitle && <span className="text-sm text-slate-500 font-normal ml-1">{subtitle}</span>}
        </p>
      </div>
    </div>
  );
}

export default Analytics;


