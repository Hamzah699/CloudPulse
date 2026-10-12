import React, { useState, useEffect } from 'react';
import { Bell, Mail, Clock, RefreshCw } from 'lucide-react';
import type { NotificationItem } from '../types';
import { api } from '../api/client';

export const NotificationBanner: React.FC = () => {
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [loading, setLoading] = useState(true);

  const loadNotifications = async () => {
    setLoading(true);
    try {
      const data = await api.getNotifications();
      setNotifications(data);
    } catch (err) {
      console.error('Failed to load notifications:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadNotifications();
  }, []);

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center">
            <Bell className="w-5 h-5 text-indigo-400 mr-2" />
            Amazon SNS Alert Dispatch History
          </h2>
          <p className="text-xs text-slate-400">
            Audit log of email alerts published to Amazon SNS topic upon incident creation or recovery.
          </p>
        </div>
        <button
          onClick={loadNotifications}
          disabled={loading}
          className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-white transition-colors"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {loading && notifications.length === 0 ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-24 rounded-2xl bg-slate-900/60 border border-slate-800 animate-pulse" />
          ))}
        </div>
      ) : notifications.length === 0 ? (
        <div className="p-12 rounded-2xl bg-slate-900/40 border border-slate-800 text-center">
          <Mail className="w-12 h-12 text-slate-500 mx-auto mb-3" />
          <h3 className="text-base font-semibold text-white">No Alert Dispatches Yet</h3>
          <p className="text-xs text-slate-400 max-w-sm mx-auto mt-1">
            When an endpoint exceeds its failure threshold, CloudPulse dispatches an SNS email alert here.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {notifications.map((n) => {
            const isResolved = n.event_type === 'INCIDENT_RESOLVED' || n.status === 'RESOLVED';
            return (
              <div
                key={n.id}
                className={`p-5 rounded-2xl border transition-all ${
                  isResolved
                    ? 'bg-emerald-950/20 border-emerald-800/60'
                    : 'bg-rose-950/20 border-rose-800/60'
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                          isResolved
                            ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                            : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                        }`}
                      >
                        {isResolved ? 'RESOLVED' : 'OUTAGE ALERT'}
                      </span>
                      <h4 className="text-sm font-bold text-white">{n.subject}</h4>
                    </div>

                    <p className="text-xs text-slate-300 font-medium">
                      Monitor: {n.monitor_name} ({n.monitor_url})
                    </p>

                    <p className="text-xs text-slate-400">
                      Reason: <span className="text-slate-200">{n.cause}</span>
                    </p>

                    <div className="flex items-center space-x-4 text-[11px] text-slate-400 pt-1">
                      <span className="flex items-center">
                        <Mail className="w-3.5 h-3.5 mr-1 text-indigo-400" />
                        Delivered to: {n.recipient}
                      </span>
                      <span className="flex items-center">
                        <Clock className="w-3.5 h-3.5 mr-1 text-slate-500" />
                        Dispatched at: {n.timestamp}
                      </span>
                      {n.duration_seconds !== null && n.duration_seconds !== undefined && (
                        <span className="text-slate-300 font-semibold">
                          Total Downtime: {n.duration_seconds}s
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
