import React from 'react';
import { Globe, Clock, ShieldCheck, AlertTriangle, TrendingUp, CheckCircle2 } from 'lucide-react';
import type { Stats } from '../types';

interface StatsOverviewProps {
  stats: Stats | null;
  loading: boolean;
}

export const StatsOverview: React.FC<StatsOverviewProps> = ({ stats, loading }) => {
  if (loading && !stats) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="h-28 rounded-2xl bg-slate-900/50 border border-slate-800 animate-pulse" />
        ))}
      </div>
    );
  }

  const total = stats?.total_monitors || 0;
  const up = stats?.up_count || 0;
  const down = stats?.down_count || 0;
  const degraded = stats?.degraded_count || 0;
  const paused = stats?.paused_count || 0;
  const uptime = stats?.overall_uptime_percentage ?? 100.0;
  const latency = stats?.average_latency_ms ?? 0;
  const incidents = stats?.open_incidents_count || 0;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
      {/* 1. Total Monitors */}
      <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 shadow-sm relative overflow-hidden group hover:border-slate-700 transition-all">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium uppercase tracking-wider text-slate-400">Total Monitors</span>
          <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400">
            <Globe className="w-5 h-5" />
          </div>
        </div>
        <div className="mt-2 flex items-baseline space-x-2">
          <span className="text-3xl font-bold tracking-tight text-white">{total}</span>
          <span className="text-xs text-slate-400">configured</span>
        </div>
        <div className="mt-3 flex items-center space-x-3 text-xs">
          <span className="flex items-center text-emerald-400">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 mr-1.5"></span>
            {up} Up
          </span>
          {down > 0 && (
            <span className="flex items-center text-rose-400 font-semibold">
              <span className="w-1.5 h-1.5 rounded-full bg-rose-400 mr-1.5"></span>
              {down} Down
            </span>
          )}
          {degraded > 0 && (
            <span className="flex items-center text-amber-400">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400 mr-1.5"></span>
              {degraded} Degraded
            </span>
          )}
          {paused > 0 && (
            <span className="flex items-center text-slate-400">
              <span className="w-1.5 h-1.5 rounded-full bg-slate-500 mr-1.5"></span>
              {paused} Paused
            </span>
          )}
        </div>
      </div>

      {/* 2. Overall Uptime */}
      <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 shadow-sm relative overflow-hidden group hover:border-slate-700 transition-all">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium uppercase tracking-wider text-slate-400">Overall Uptime</span>
          <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-400">
            <ShieldCheck className="w-5 h-5" />
          </div>
        </div>
        <div className="mt-2 flex items-baseline space-x-2">
          <span className={`text-3xl font-bold tracking-tight ${uptime >= 99 ? 'text-emerald-400' : uptime >= 95 ? 'text-amber-400' : 'text-rose-400'}`}>
            {uptime.toFixed(1)}%
          </span>
          <span className="text-xs text-slate-400">SLA target: 99.9%</span>
        </div>
        <div className="mt-3 flex items-center text-xs text-slate-400">
          <TrendingUp className="w-3.5 h-3.5 text-emerald-400 mr-1.5" />
          <span>Real DynamoDB telemetry</span>
        </div>
      </div>

      {/* 3. Average Response Time */}
      <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 shadow-sm relative overflow-hidden group hover:border-slate-700 transition-all">
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium uppercase tracking-wider text-slate-400">Avg Latency</span>
          <div className="p-2 rounded-xl bg-cyan-500/10 text-cyan-400">
            <Clock className="w-5 h-5" />
          </div>
        </div>
        <div className="mt-2 flex items-baseline space-x-2">
          <span className="text-3xl font-bold tracking-tight text-white">
            {latency > 0 ? `${Math.round(latency)}` : '—'}
          </span>
          <span className="text-xs text-slate-400">{latency > 0 ? 'ms' : 'No data yet'}</span>
        </div>
        <div className="mt-3 flex items-center text-xs text-slate-400">
          <span className="text-cyan-400 font-medium mr-1.5">DNS + TCP + TTFB</span>
          <span>high-res socket probe</span>
        </div>
      </div>

      {/* 4. Active Incidents */}
      <div className={`p-5 rounded-2xl border shadow-sm relative overflow-hidden group transition-all ${
        incidents === 0
          ? 'bg-slate-900/60 border-slate-800/80 hover:border-slate-700'
          : 'bg-rose-950/20 border-rose-800/50 hover:border-rose-700'
      }`}>
        <div className="flex items-center justify-between">
          <span className="text-xs font-medium uppercase tracking-wider text-slate-400">Active Incidents</span>
          <div className={`p-2 rounded-xl ${incidents === 0 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'}`}>
            {incidents === 0 ? <CheckCircle2 className="w-5 h-5" /> : <AlertTriangle className="w-5 h-5 animate-bounce" />}
          </div>
        </div>
        <div className="mt-2 flex items-baseline space-x-2">
          <span className={`text-3xl font-bold tracking-tight ${incidents === 0 ? 'text-white' : 'text-rose-400'}`}>
            {incidents}
          </span>
          <span className="text-xs text-slate-400">{incidents === 0 ? 'outages' : 'open incidents'}</span>
        </div>
        <div className="mt-3 flex items-center text-xs">
          {incidents === 0 ? (
            <span className="text-emerald-400">No active incidents detected</span>
          ) : (
            <span className="text-rose-400 font-medium">SNS alerts actively dispatched</span>
          )}
        </div>
      </div>
    </div>
  );
};
