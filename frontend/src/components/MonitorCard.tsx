import React, { useState } from 'react';
import { ExternalLink, Play, Pause, Trash2, Edit3, BarChart2, RefreshCw, XCircle, AlertCircle, Clock, Zap } from 'lucide-react';
import type { Monitor } from '../types';

interface MonitorCardProps {
  monitor: Monitor;
  onCheckNow: (id: string) => Promise<void>;
  onPause: (id: string) => Promise<void>;
  onResume: (id: string) => Promise<void>;
  onEdit: (monitor: Monitor) => void;
  onDelete: (id: string) => Promise<void>;
  onViewAnalytics: (monitor: Monitor) => void;
}

export const MonitorCard: React.FC<MonitorCardProps> = ({
  monitor,
  onCheckNow,
  onPause,
  onResume,
  onEdit,
  onDelete,
  onViewAnalytics,
}) => {
  const [checking, setChecking] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const handleCheck = async () => {
    setChecking(true);
    try {
      await onCheckNow(monitor.id);
    } finally {
      setChecking(false);
    }
  };

  const handleDelete = async () => {
    if (window.confirm(`Are you sure you want to delete monitor "${monitor.name}"?`)) {
      setDeleting(true);
      try {
        await onDelete(monitor.id);
      } finally {
        setDeleting(false);
      }
    }
  };

  const getStatusBadge = () => {
    switch (monitor.status) {
      case 'UP':
        return (
          <span className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>OPERATIONAL</span>
          </span>
        );
      case 'DOWN':
        return (
          <span className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
            <XCircle className="w-3.5 h-3.5" />
            <span>DOWN</span>
          </span>
        );
      case 'DEGRADED':
        return (
          <span className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <AlertCircle className="w-3.5 h-3.5" />
            <span>DEGRADED</span>
          </span>
        );
      case 'PAUSED':
        return (
          <span className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-500/10 text-slate-400 border border-slate-500/20">
            <Pause className="w-3.5 h-3.5" />
            <span>PAUSED</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
            <Clock className="w-3.5 h-3.5" />
            <span>PENDING</span>
          </span>
        );
    }
  };

  const formatLastChecked = (iso?: string | null) => {
    if (!iso) return 'Never';
    try {
      const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
      if (diff < 60) return `${diff}s ago`;
      if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
      return `${Math.floor(diff / 3600)}h ago`;
    } catch {
      return iso;
    }
  };

  return (
    <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800/80 hover:border-slate-700/80 transition-all shadow-sm flex flex-col justify-between">
      <div>
        {/* Header: Name, Method, Status */}
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0 flex-1">
            <div className="flex items-center space-x-2">
              <span className="px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                {monitor.method}
              </span>
              <h3 className="text-base font-semibold text-white truncate" title={monitor.name}>
                {monitor.name}
              </h3>
            </div>
            <a
              href={monitor.url}
              target="_blank"
              rel="noreferrer"
              className="mt-1 flex items-center space-x-1 text-xs text-slate-400 hover:text-indigo-400 transition-colors truncate max-w-sm"
              title={monitor.url}
            >
              <span className="truncate">{monitor.url}</span>
              <ExternalLink className="w-3 h-3 flex-shrink-0" />
            </a>
          </div>
          <div>{getStatusBadge()}</div>
        </div>

        {/* Tags */}
        {monitor.tags && monitor.tags.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1.5">
            {monitor.tags.map((tag, idx) => (
              <span key={idx} className="px-2 py-0.5 rounded-md text-[10px] font-medium bg-slate-800 text-slate-300 border border-slate-700/50">
                #{tag}
              </span>
            ))}
          </div>
        )}

        {/* Real-time Metrics Grid */}
        <div className="mt-4 grid grid-cols-3 gap-2 p-3 rounded-xl bg-slate-950/60 border border-slate-800/50">
          <div>
            <span className="text-[10px] uppercase tracking-wider text-slate-400 block">Latency</span>
            <span className="text-sm font-bold text-white font-mono flex items-center mt-0.5">
              <Zap className="w-3 h-3 text-cyan-400 mr-1" />
              {monitor.last_latency_ms ? `${Math.round(monitor.last_latency_ms)}ms` : '—'}
            </span>
          </div>

          <div>
            <span className="text-[10px] uppercase tracking-wider text-slate-400 block">Uptime</span>
            <span className={`text-sm font-bold font-mono mt-0.5 block ${
              monitor.uptime_percentage >= 99 ? 'text-emerald-400' : 'text-amber-400'
            }`}>
              {monitor.uptime_percentage.toFixed(1)}%
            </span>
          </div>

          <div>
            <span className="text-[10px] uppercase tracking-wider text-slate-400 block">Status Code</span>
            <span className="text-sm font-bold font-mono text-slate-200 mt-0.5 block">
              {monitor.last_status_code ? `${monitor.last_status_code}` : '—'}
            </span>
          </div>
        </div>

        <div className="mt-3 flex items-center justify-between text-[11px] text-slate-400">
          <span>Interval: {monitor.interval_seconds}s</span>
          <span>Checked: {formatLastChecked(monitor.last_checked_at)}</span>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="mt-5 pt-3 border-t border-slate-800/60 flex items-center justify-between">
        <button
          onClick={handleCheck}
          disabled={checking || monitor.status === 'PAUSED'}
          className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-indigo-600/20 text-indigo-300 hover:bg-indigo-600/30 border border-indigo-500/30 text-xs font-medium transition-colors disabled:opacity-40"
          title="Run real HTTP health check immediately"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${checking ? 'animate-spin' : ''}`} />
          <span>{checking ? 'Testing...' : 'Test Now'}</span>
        </button>

        <div className="flex items-center space-x-1">
          <button
            onClick={() => onViewAnalytics(monitor)}
            className="p-1.5 rounded-lg text-slate-400 hover:text-cyan-400 hover:bg-slate-800 transition-colors"
            title="View Latency Charts & Check History"
          >
            <BarChart2 className="w-4 h-4" />
          </button>

          {monitor.status === 'PAUSED' ? (
            <button
              onClick={() => onResume(monitor.id)}
              className="p-1.5 rounded-lg text-slate-400 hover:text-emerald-400 hover:bg-slate-800 transition-colors"
              title="Resume Monitoring"
            >
              <Play className="w-4 h-4" />
            </button>
          ) : (
            <button
              onClick={() => onPause(monitor.id)}
              className="p-1.5 rounded-lg text-slate-400 hover:text-amber-400 hover:bg-slate-800 transition-colors"
              title="Pause Monitoring"
            >
              <Pause className="w-4 h-4" />
            </button>
          )}

          <button
            onClick={() => onEdit(monitor)}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
            title="Edit Monitor Config"
          >
            <Edit3 className="w-4 h-4" />
          </button>

          <button
            onClick={handleDelete}
            disabled={deleting}
            className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition-colors disabled:opacity-40"
            title="Delete Monitor"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
