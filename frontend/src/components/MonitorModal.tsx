import React, { useState, useEffect } from 'react';
import { X, ShieldAlert, ShieldCheck, AlertCircle } from 'lucide-react';
import type { Monitor } from '../types';
import { api } from '../api/client';

interface MonitorModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (monitorData: Partial<Monitor>) => Promise<void>;
  initialData?: Monitor | null;
}

export const MonitorModal: React.FC<MonitorModalProps> = ({
  isOpen,
  onClose,
  onSave,
  initialData,
}) => {
  const [name, setName] = useState('');
  const [url, setUrl] = useState('');
  const [method, setMethod] = useState('GET');
  const [interval, setInterval] = useState(60);
  const [timeout, setTimeoutVal] = useState(10);
  const [expectedStatus, setExpectedStatus] = useState(200);
  const [alertEmail, setAlertEmail] = useState('');
  const [failureThreshold, setFailureThreshold] = useState(2);
  const [recoveryThreshold, setRecoveryThreshold] = useState(2);
  const [tags, setTags] = useState('');
  const [headers, setHeaders] = useState('');
  const [body, setBody] = useState('');

  const [validatingSSRF, setValidatingSSRF] = useState(false);
  const [ssrfResult, setSsrfResult] = useState<{ is_valid: boolean; message: string; ips: string[] } | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (initialData) {
      setName(initialData.name);
      setUrl(initialData.url);
      setMethod(initialData.method || 'GET');
      setInterval(initialData.interval_seconds || 60);
      setTimeoutVal(initialData.timeout_seconds || 10);
      setExpectedStatus(initialData.expected_status || 200);
      setAlertEmail(initialData.alert_email || '');
      setFailureThreshold(initialData.failure_threshold || 2);
      setRecoveryThreshold(initialData.recovery_threshold || 2);
      setTags((initialData.tags || []).join(', '));
      setHeaders(initialData.headers ? JSON.stringify(initialData.headers, null, 2) : '');
      setBody(initialData.body || '');
      setSsrfResult(null);
    } else {
      setName('');
      setUrl('');
      setMethod('GET');
      setInterval(60);
      setTimeoutVal(10);
      setExpectedStatus(200);
      setAlertEmail('');
      setFailureThreshold(2);
      setRecoveryThreshold(2);
      setTags('production, api');
      setHeaders('');
      setBody('');
      setSsrfResult(null);
    }
    setError(null);
  }, [initialData, isOpen]);

  if (!isOpen) return null;

  const handleValidateSSRF = async () => {
    if (!url.trim()) return;
    setValidatingSSRF(true);
    setError(null);
    try {
      const res = await api.validateUrlSSRF(url.trim());
      if (res.is_valid) {
        setSsrfResult({
          is_valid: true,
          message: `Safe to probe. Resolved IP(s): ${res.resolved_ips.join(', ')}`,
          ips: res.resolved_ips,
        });
      } else {
        setSsrfResult({
          is_valid: false,
          message: res.error || 'Blocked by SSRF security policy',
          ips: res.resolved_ips || [],
        });
      }
    } catch (err: any) {
      setSsrfResult({
        is_valid: false,
        message: err.message || 'Validation failed',
        ips: [],
      });
    } finally {
      setValidatingSSRF(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!name.trim()) {
      setError('Monitor name is required.');
      return;
    }
    if (!url.trim()) {
      setError('Target URL is required.');
      return;
    }

    let parsedHeaders = {};
    if (headers.trim()) {
      try {
        parsedHeaders = JSON.parse(headers);
      } catch {
        setError('Headers must be valid JSON format (e.g. {"Authorization": "Bearer ..."})');
        return;
      }
    }

    const parsedTags = tags
      .split(',')
      .map((t) => t.trim())
      .filter((t) => t.length > 0);

    setSubmitting(true);
    try {
      await onSave({
        name: name.trim(),
        url: url.trim(),
        method,
        interval_seconds: Number(interval),
        timeout_seconds: Number(timeout),
        expected_status: Number(expectedStatus),
        alert_email: alertEmail.trim() || null,
        failure_threshold: Number(failureThreshold),
        recovery_threshold: Number(recoveryThreshold),
        tags: parsedTags,
        headers: parsedHeaders,
        body: body.trim() || null,
      });
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to save monitor');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="relative w-full max-w-2xl rounded-2xl bg-slate-900 border border-slate-800 shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800">
          <div>
            <h2 className="text-lg font-bold text-white">
              {initialData ? 'Edit Monitor Configuration' : 'Create New Health Monitor'}
            </h2>
            <p className="text-xs text-slate-400">
              Provision high-frequency serverless HTTP uptime probing with SSRF guard.
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4 max-h-[80vh] overflow-y-auto">
          {error && (
            <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Name & URL */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Monitor Friendly Name *
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Production Billing API"
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:border-indigo-500 transition-colors"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                HTTP Method
              </label>
              <select
                value={method}
                onChange={(e) => setMethod(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:border-indigo-500 transition-colors"
              >
                <option value="GET">GET (Standard ping)</option>
                <option value="HEAD">HEAD (Lightweight headers only)</option>
                <option value="POST">POST (API with payload)</option>
                <option value="PUT">PUT</option>
              </select>
            </div>
          </div>

          {/* Target URL with SSRF Guard */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-xs font-semibold text-slate-300">
                Target Endpoint URL *
              </label>
              <button
                type="button"
                onClick={handleValidateSSRF}
                disabled={validatingSSRF || !url}
                className="text-xs text-indigo-400 hover:text-indigo-300 underline font-medium disabled:opacity-40"
              >
                {validatingSSRF ? 'Verifying IP...' : 'Test SSRF Safety'}
              </button>
            </div>
            <input
              type="url"
              value={url}
              onChange={(e) => {
                setUrl(e.target.value);
                setSsrfResult(null);
              }}
              onBlur={handleValidateSSRF}
              placeholder="https://api.yourdomain.com/health"
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm font-mono focus:outline-none focus:border-indigo-500 transition-colors"
              required
            />

            {/* SSRF Feedback Banner */}
            {ssrfResult && (
              <div
                className={`mt-2 p-2.5 rounded-xl border text-xs flex items-center space-x-2 ${
                  ssrfResult.is_valid
                    ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-300'
                    : 'bg-rose-500/10 border-rose-500/20 text-rose-300'
                }`}
              >
                {ssrfResult.is_valid ? (
                  <ShieldCheck className="w-4 h-4 flex-shrink-0 text-emerald-400" />
                ) : (
                  <ShieldAlert className="w-4 h-4 flex-shrink-0 text-rose-400" />
                )}
                <span>{ssrfResult.message}</span>
              </div>
            )}
            <p className="mt-1 text-[11px] text-slate-500">
              SSRF Guard enforces DNS resolution check and rejects loopback (127.0.0.1), private RFC1918, and AWS metadata (169.254.169.254).
            </p>
          </div>

          {/* Interval, Timeout, Expected Status */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Interval (EventBridge)
              </label>
              <select
                value={interval}
                onChange={(e) => setInterval(Number(e.target.value))}
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:border-indigo-500"
              >
                <option value={60}>Every 1 minute</option>
                <option value={300}>Every 5 minutes</option>
                <option value={900}>Every 15 minutes</option>
                <option value={1800}>Every 30 minutes</option>
                <option value={3600}>Every 60 minutes</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Timeout (seconds)
              </label>
              <select
                value={timeout}
                onChange={(e) => setTimeoutVal(Number(e.target.value))}
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:border-indigo-500"
              >
                <option value={3}>3 seconds (Strict SLA)</option>
                <option value={5}>5 seconds</option>
                <option value={10}>10 seconds (Standard)</option>
                <option value={15}>15 seconds</option>
                <option value={30}>30 seconds (Max)</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Expected HTTP Code
              </label>
              <input
                type="number"
                value={expectedStatus}
                onChange={(e) => setExpectedStatus(Number(e.target.value))}
                className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:border-indigo-500 font-mono"
              />
            </div>
          </div>

          {/* Incident Thresholds & Alert Email */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 p-4 rounded-xl bg-slate-950/50 border border-slate-800/60">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Failure Threshold
              </label>
              <input
                type="number"
                min={1}
                max={10}
                value={failureThreshold}
                onChange={(e) => setFailureThreshold(Number(e.target.value))}
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-white text-sm focus:outline-none focus:border-indigo-500 font-mono"
              />
              <span className="text-[10px] text-slate-400">Failed checks to open incident</span>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Recovery Threshold
              </label>
              <input
                type="number"
                min={1}
                max={10}
                value={recoveryThreshold}
                onChange={(e) => setRecoveryThreshold(Number(e.target.value))}
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-white text-sm focus:outline-none focus:border-indigo-500 font-mono"
              />
              <span className="text-[10px] text-slate-400">Passes to auto-resolve</span>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Alert Email (SNS)
              </label>
              <input
                type="email"
                value={alertEmail}
                onChange={(e) => setAlertEmail(e.target.value)}
                placeholder="devops@domain.com"
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-white text-sm focus:outline-none focus:border-indigo-500"
              />
              <span className="text-[10px] text-slate-400">Receives outage & recovery emails</span>
            </div>
          </div>

          {/* Tags */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1">
              Tags (Comma separated)
            </label>
            <input
              type="text"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              placeholder="e.g. prod, external, critical"
              className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:border-indigo-500"
            />
          </div>

          {/* Optional: Headers & Body */}
          <details className="text-xs text-slate-400 group">
            <summary className="cursor-pointer text-indigo-400 hover:text-indigo-300 font-semibold mb-2">
              Advanced: Custom HTTP Headers & Body
            </summary>
            <div className="space-y-3 pt-2">
              <div>
                <label className="block text-[11px] font-semibold text-slate-300 mb-1">
                  Custom Request Headers (JSON)
                </label>
                <textarea
                  value={headers}
                  onChange={(e) => setHeaders(e.target.value)}
                  placeholder={'{\n  "X-Custom-Header": "CloudPulsePing",\n  "Authorization": "Bearer token"\n}'}
                  rows={3}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white font-mono text-xs focus:outline-none focus:border-indigo-500"
                />
              </div>

              {['POST', 'PUT', 'PATCH'].includes(method) && (
                <div>
                  <label className="block text-[11px] font-semibold text-slate-300 mb-1">
                    Request Body (Payload)
                  </label>
                  <textarea
                    value={body}
                    onChange={(e) => setBody(e.target.value)}
                    placeholder='{"action": "ping"}'
                    rows={2}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white font-mono text-xs focus:outline-none focus:border-indigo-500"
                  />
                </div>
              )}
            </div>
          </details>

          {/* Action buttons */}
          <div className="pt-4 border-t border-slate-800 flex items-center justify-end space-x-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-5 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/20 transition-all disabled:opacity-50"
            >
              {submitting ? 'Saving...' : initialData ? 'Update Monitor' : 'Create Monitor'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
