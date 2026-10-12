import React, { useState, useEffect } from 'react';
import { AlertTriangle, CheckCircle, Clock, ShieldCheck, Mail, Check, RefreshCw } from 'lucide-react';
import type { Incident } from '../types';
import { api } from '../api/client';

export const IncidentList: React.FC = () => {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [filter, setFilter] = useState<'ALL' | 'OPEN' | 'RESOLVED'>('ALL');
  const [loading, setLoading] = useState(true);
  const [acknowledgingId, setAcknowledgingId] = useState<string | null>(null);

  const loadIncidents = async () => {
    setLoading(true);
    try {
      const data = await api.getIncidents(filter === 'ALL' ? undefined : filter);
      setIncidents(data);
    } catch (err) {
      console.error('Failed to load incidents:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadIncidents();
  }, [filter]);

  const handleAcknowledge = async (id: string) => {
    setAcknowledgingId(id);
    try {
      const updated = await api.acknowledgeIncident(id);
      setIncidents((prev) => prev.map((inc) => (inc.id === id ? updated : inc)));
    } catch (err) {
      console.error('Failed to acknowledge incident:', err);
    } finally {
      setAcknowledgingId(null);
    }
  };

  const formatDuration = (seconds?: number | null) => {
    if (!seconds && seconds !== 0) return 'Ongoing';
    if (seconds < 60) return `${seconds}s`;
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  return (
    <div className="space-y-6">
      {/* Header and Filter */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center">
            <AlertTriangle className="w-5 h-5 text-rose-400 mr-2" />
            Incidents & Outage Records
          </h2>
          <p className="text-xs text-slate-400">
            Real-time incident state machine tracking consecutive check failures and SNS notifications.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <div className="flex rounded-xl bg-slate-900 p-1 border border-slate-800">
            {(['ALL', 'OPEN', 'RESOLVED'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setFilter(tab)}
                className={`px-3 py-1 rounded-lg text-xs font-semibold transition-colors ${
                  filter === tab
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>

          <button
            onClick={loadIncidents}
            disabled={loading}
            className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white transition-colors"
            title="Refresh Incidents"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Incident List Cards */}
      {loading && incidents.length === 0 ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-28 rounded-2xl bg-slate-900/60 border border-slate-800 animate-pulse" />
          ))}
        </div>
      ) : incidents.length === 0 ? (
        <div className="p-12 rounded-2xl bg-slate-900/40 border border-slate-800 text-center">
          <ShieldCheck className="w-12 h-12 text-emerald-400 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-white">No Incidents Found</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto mt-1">
            All endpoints are operational and meeting SLA thresholds. No downtime detected for this view.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {incidents.map((inc) => (
            <div
              key={inc.id}
              className={`p-5 rounded-2xl border transition-all ${
                inc.status === 'OPEN'
                  ? 'bg-rose-950/20 border-rose-800/60 shadow-lg shadow-rose-950/20'
                  : inc.status === 'ACKNOWLEDGED'
                  ? 'bg-amber-950/20 border-amber-800/60'
                  : 'bg-slate-900/60 border-slate-800/80'
              }`}
            >
              <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
                <div className="space-y-1.5 flex-1">
                  <div className="flex items-center space-x-2">
                    <span
                      className={`px-2.5 py-0.5 rounded-full text-xs font-bold tracking-wide uppercase ${
                        inc.status === 'OPEN'
                          ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30 animate-pulse'
                          : inc.status === 'ACKNOWLEDGED'
                          ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                          : 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                      }`}
                    >
                      {inc.status}
                    </span>
                    <h3 className="text-base font-semibold text-white">{inc.monitor_name}</h3>
                  </div>

                  <p className="text-xs text-slate-400 font-mono">{inc.monitor_url}</p>

                  <div className="p-2.5 rounded-xl bg-slate-950/80 border border-slate-800/60 text-xs">
                    <span className="text-rose-400 font-semibold">Root Cause: </span>
                    <span className="text-slate-200">{inc.cause}</span>
                    {inc.last_status_code && (
                      <span className="ml-2 px-1.5 py-0.2 rounded bg-slate-800 text-slate-300 font-mono text-[11px]">
                        HTTP {inc.last_status_code}
                      </span>
                    )}
                  </div>

                  <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-slate-400 pt-1">
                    <span className="flex items-center">
                      <Clock className="w-3.5 h-3.5 mr-1 text-slate-500" />
                      Started: {inc.started_at}
                    </span>

                    {inc.resolved_at && (
                      <span className="flex items-center text-emerald-400">
                        <CheckCircle className="w-3.5 h-3.5 mr-1" />
                        Resolved: {inc.resolved_at}
                      </span>
                    )}

                    <span className="font-semibold text-slate-300">
                      Duration: {formatDuration(inc.duration_seconds)}
                    </span>

                    <span className="text-slate-400">
                      Failed Checks: {inc.consecutive_failures}
                    </span>

                    {inc.alert_recipient && (
                      <span className="flex items-center text-indigo-400">
                        <Mail className="w-3.5 h-3.5 mr-1" />
                        SNS: {inc.alert_recipient}
                      </span>
                    )}
                  </div>
                </div>

                {/* Actions */}
                {inc.status === 'OPEN' && (
                  <button
                    onClick={() => handleAcknowledge(inc.id)}
                    disabled={acknowledgingId === inc.id}
                    className="self-start sm:self-center px-3.5 py-1.5 rounded-xl bg-amber-600/20 text-amber-300 hover:bg-amber-600/30 border border-amber-500/30 text-xs font-semibold transition-colors flex items-center space-x-1.5 disabled:opacity-40"
                  >
                    <Check className="w-3.5 h-3.5" />
                    <span>{acknowledgingId === inc.id ? 'Saving...' : 'Acknowledge'}</span>
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
