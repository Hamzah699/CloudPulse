import React, { useState, useEffect } from 'react';
import { X, RefreshCw, Activity, CheckCircle2, XCircle } from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import type { Monitor, CheckResult } from '../types';
import { api } from '../api/client';

interface MonitorDetailModalProps {
  monitor: Monitor | null;
  isOpen: boolean;
  onClose: () => void;
  onCheckNow: (id: string) => Promise<void>;
}

export const MonitorDetailModal: React.FC<MonitorDetailModalProps> = ({
  monitor,
  isOpen,
  onClose,
  onCheckNow,
}) => {
  const [checks, setChecks] = useState<CheckResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [checking, setChecking] = useState(false);

  const loadChecks = async () => {
    if (!monitor) return;
    setLoading(true);
    try {
      const data = await api.getChecks(monitor.id, 40);
      setChecks(data);
    } catch (err) {
      console.error('Failed to load checks:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen && monitor) {
      loadChecks();
    }
  }, [isOpen, monitor]);

  if (!isOpen || !monitor) return null;

  const handleCheck = async () => {
    setChecking(true);
    try {
      await onCheckNow(monitor.id);
      await loadChecks();
    } finally {
      setChecking(false);
    }
  };

  // Prepare chart data (reverse checks so chronological from left to right)
  const chartData = [...checks].reverse().map((c) => ({
    time: c.timestamp ? c.timestamp.substring(11, 19) : '',
    latency: Math.round(c.latency_ms),
    dns: Math.round(c.dns_time_ms),
    ttfb: Math.round(c.ttfb_ms),
    status: c.status,
    code: c.status_code || 0,
  }));

  const latencies = checks.map((c) => c.latency_ms).filter((l) => l > 0);
  const avgLatency = latencies.length > 0 ? Math.round(latencies.reduce((a, b) => a + b, 0) / latencies.length) : 0;
  const minLatency = latencies.length > 0 ? Math.round(Math.min(...latencies)) : 0;
  const maxLatency = latencies.length > 0 ? Math.round(Math.max(...latencies)) : 0;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="relative w-full max-w-4xl rounded-2xl bg-slate-900 border border-slate-800 shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-900/60">
          <div>
            <div className="flex items-center space-x-2">
              <span className="px-2 py-0.5 rounded text-xs font-mono font-bold bg-indigo-500/20 text-indigo-300">
                {monitor.method}
              </span>
              <h2 className="text-xl font-bold text-white">{monitor.name}</h2>
            </div>
            <p className="text-xs text-slate-400 font-mono mt-0.5">{monitor.url}</p>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={handleCheck}
              disabled={checking}
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-indigo-600/20 text-indigo-300 hover:bg-indigo-600/30 border border-indigo-500/30 text-xs font-medium transition-colors disabled:opacity-40"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${checking ? 'animate-spin' : ''}`} />
              <span>{checking ? 'Probing...' : 'Run Probe Now'}</span>
            </button>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content Body */}
        <div className="p-6 space-y-6 max-h-[82vh] overflow-y-auto">
          {/* Key Metrics Strip */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800">
              <span className="text-[10px] uppercase tracking-wider text-slate-400 block">Average Latency</span>
              <span className="text-xl font-bold text-white font-mono mt-1 block">
                {avgLatency > 0 ? `${avgLatency} ms` : '—'}
              </span>
            </div>
            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800">
              <span className="text-[10px] uppercase tracking-wider text-slate-400 block">Min / Max Latency</span>
              <span className="text-xl font-bold text-cyan-400 font-mono mt-1 block">
                {minLatency} / {maxLatency} <span className="text-xs text-slate-400">ms</span>
              </span>
            </div>
            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800">
              <span className="text-[10px] uppercase tracking-wider text-slate-400 block">Uptime Rate</span>
              <span className={`text-xl font-bold font-mono mt-1 block ${
                monitor.uptime_percentage >= 99 ? 'text-emerald-400' : 'text-amber-400'
              }`}>
                {monitor.uptime_percentage.toFixed(1)}%
              </span>
            </div>
            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800">
              <span className="text-[10px] uppercase tracking-wider text-slate-400 block">Total Checks</span>
              <span className="text-xl font-bold text-slate-200 font-mono mt-1 block">
                {monitor.total_checks}
              </span>
            </div>
          </div>

          {/* Recharts Latency Trend Chart */}
          <div className="p-5 rounded-2xl bg-slate-950/80 border border-slate-800">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-sm font-semibold text-white flex items-center">
                  <Activity className="w-4 h-4 text-indigo-400 mr-2" />
                  Latency Trend & Response History
                </h3>
                <p className="text-xs text-slate-400">Real-time socket probe latency (DNS + TCP + TTFB)</p>
              </div>
              <div className="text-xs text-slate-400 font-mono">
                Last {chartData.length} Data Points
              </div>
            </div>

            {chartData.length > 0 ? (
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                    <defs>
                      <linearGradient id="latencyGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
                        <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                    <XAxis
                      dataKey="time"
                      stroke="#64748b"
                      fontSize={11}
                      tickLine={false}
                    />
                    <YAxis
                      stroke="#64748b"
                      fontSize={11}
                      tickLine={false}
                      unit="ms"
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#0f172a',
                        borderColor: '#334155',
                        borderRadius: '0.75rem',
                        fontSize: '12px',
                      }}
                      itemStyle={{ color: '#e2e8f0' }}
                    />
                    <Area
                      type="monotone"
                      dataKey="latency"
                      name="Response Time"
                      stroke="#818cf8"
                      strokeWidth={2}
                      fillOpacity={1}
                      fill="url(#latencyGradient)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="h-48 flex items-center justify-center text-slate-500 text-xs">
                No latency history recorded yet. Click "Run Probe Now" above.
              </div>
            )}
          </div>

          {/* Historical Checks Table */}
          <div className="rounded-2xl bg-slate-950/80 border border-slate-800 overflow-hidden">
            <div className="px-5 py-3 border-b border-slate-800/80 flex items-center justify-between">
              <h3 className="text-xs font-semibold text-white uppercase tracking-wider">
                Telemetry Log (DynamoDB History)
              </h3>
              <span className="text-xs text-slate-400">Retention: 30 Days (DynamoDB TTL)</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-900/50 text-slate-400 font-semibold border-b border-slate-800/60">
                  <tr>
                    <th className="py-2.5 px-4">Status</th>
                    <th className="py-2.5 px-4">Timestamp (UTC)</th>
                    <th className="py-2.5 px-4">HTTP Code</th>
                    <th className="py-2.5 px-4">Latency</th>
                    <th className="py-2.5 px-4">DNS</th>
                    <th className="py-2.5 px-4">TTFB</th>
                    <th className="py-2.5 px-4">Resolved IP</th>
                    <th className="py-2.5 px-4">Notes</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/40 text-slate-300 font-mono">
                  {loading ? (
                    <tr>
                      <td colSpan={8} className="py-8 text-center text-slate-500">
                        Loading check records...
                      </td>
                    </tr>
                  ) : checks.length === 0 ? (
                    <tr>
                      <td colSpan={8} className="py-8 text-center text-slate-500">
                        No health checks executed yet.
                      </td>
                    </tr>
                  ) : (
                    checks.map((c) => (
                      <tr key={c.id} className="hover:bg-slate-900/30 transition-colors">
                        <td className="py-2 px-4">
                          {c.status === 'UP' ? (
                            <span className="inline-flex items-center text-emerald-400 font-semibold">
                              <CheckCircle2 className="w-3.5 h-3.5 mr-1" /> UP
                            </span>
                          ) : (
                            <span className="inline-flex items-center text-rose-400 font-semibold">
                              <XCircle className="w-3.5 h-3.5 mr-1" /> DOWN
                            </span>
                          )}
                        </td>
                        <td className="py-2 px-4 text-slate-400">{c.timestamp}</td>
                        <td className="py-2 px-4">
                          <span className={`px-1.5 py-0.5 rounded text-[11px] ${
                            c.status_code === 200 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'
                          }`}>
                            {c.status_code || 'Err'}
                          </span>
                        </td>
                        <td className="py-2 px-4 font-bold text-white">{Math.round(c.latency_ms)}ms</td>
                        <td className="py-2 px-4 text-slate-400">{Math.round(c.dns_time_ms)}ms</td>
                        <td className="py-2 px-4 text-slate-400">{Math.round(c.ttfb_ms)}ms</td>
                        <td className="py-2 px-4 text-slate-400">{c.target_ip || '—'}</td>
                        <td className="py-2 px-4 text-slate-400 truncate max-w-xs font-sans">
                          {c.error_message || 'OK'}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
