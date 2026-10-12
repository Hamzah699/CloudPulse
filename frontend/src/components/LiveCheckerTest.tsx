import React, { useState } from 'react';
import { Shield, ShieldAlert, ShieldCheck, ArrowRight } from 'lucide-react';
import { api } from '../api/client';

export const LiveCheckerTest: React.FC = () => {
  const [testUrl, setTestUrl] = useState('https://dns.google');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any | null>(null);

  const presets = [
    { label: 'Google DNS (Safe)', url: 'https://dns.google', type: 'safe' },
    { label: 'Cloudflare (Safe)', url: 'https://1.1.1.1', type: 'safe' },
    { label: 'AWS Metadata (SSRF Attack)', url: 'http://169.254.169.254/latest/meta-data', type: 'attack' },
    { label: 'Localhost (SSRF Attack)', url: 'http://127.0.0.1:8080/admin', type: 'attack' },
    { label: 'Private LAN (SSRF Attack)', url: 'http://192.168.1.1/router', type: 'attack' },
  ];

  const runTest = async (urlToTest: string) => {
    setLoading(true);
    setResult(null);
    try {
      const data = await api.validateUrlSSRF(urlToTest);
      setResult(data);
    } catch (err: any) {
      setResult({
        url: urlToTest,
        is_valid: false,
        error: err.message || 'Validation request failed',
        resolved_ips: [],
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Intro Header */}
      <div>
        <h2 className="text-xl font-bold text-white flex items-center">
          <Shield className="w-5 h-5 text-indigo-400 mr-2" />
          SSRF Guard & Security Verification Sandbox
        </h2>
        <p className="text-xs text-slate-400 mt-1">
          Demonstrate and verify real-time Server-Side Request Forgery (SSRF) defense: DNS address resolution,
          private IPv4/IPv6 block checking, AWS IMDS (169.254.169.254) isolation, and safe redirect following.
        </p>
      </div>

      {/* Input & Preset Buttons */}
      <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-4">
        <div>
          <label className="block text-xs font-semibold text-slate-300 mb-1">
            Target URL to Probe
          </label>
          <div className="flex space-x-2">
            <input
              type="text"
              value={testUrl}
              onChange={(e) => setTestUrl(e.target.value)}
              placeholder="e.g. https://api.github.com or http://169.254.169.254"
              className="flex-1 px-4 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white font-mono text-sm focus:outline-none focus:border-indigo-500"
            />
            <button
              onClick={() => runTest(testUrl)}
              disabled={loading || !testUrl}
              className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center space-x-2 transition-colors disabled:opacity-50"
            >
              {loading ? (
                <span>Validating...</span>
              ) : (
                <>
                  <span>Verify Security</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </div>

        {/* Quick Test Presets */}
        <div>
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-2">
            Quick Security Presets (Click to Test)
          </span>
          <div className="flex flex-wrap gap-2">
            {presets.map((p, idx) => (
              <button
                key={idx}
                onClick={() => {
                  setTestUrl(p.url);
                  runTest(p.url);
                }}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
                  p.type === 'safe'
                    ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20 hover:bg-emerald-500/20'
                    : 'bg-rose-500/10 text-rose-300 border-rose-500/20 hover:bg-rose-500/20'
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Result Display */}
      {result && (
        <div
          className={`p-6 rounded-2xl border transition-all ${
            result.is_valid
              ? 'bg-emerald-950/20 border-emerald-800/60'
              : 'bg-rose-950/20 border-rose-800/60 shadow-xl shadow-rose-950/20'
          }`}
        >
          <div className="flex items-start space-x-3">
            {result.is_valid ? (
              <div className="p-2 rounded-xl bg-emerald-500/20 text-emerald-400 flex-shrink-0">
                <ShieldCheck className="w-6 h-6" />
              </div>
            ) : (
              <div className="p-2 rounded-xl bg-rose-500/20 text-rose-400 flex-shrink-0">
                <ShieldAlert className="w-6 h-6" />
              </div>
            )}

            <div className="space-y-2 flex-1">
              <div>
                <h3
                  className={`text-base font-bold ${
                    result.is_valid ? 'text-emerald-300' : 'text-rose-300'
                  }`}
                >
                  {result.is_valid ? 'SSRF Validation Passed' : 'Security Alert: Request Blocked'}
                </h3>
                <p className="text-xs text-slate-300 mt-0.5">
                  {result.is_valid
                    ? 'Target endpoint is verified safe for public cloud probing.'
                    : result.error || 'Blocked by CloudPulse SSRF Defense Engine.'}
                </p>
              </div>

              {/* Resolved IPs */}
              {result.resolved_ips && result.resolved_ips.length > 0 && (
                <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800/80 text-xs font-mono space-y-1">
                  <span className="text-slate-400 block text-[11px] font-sans">
                    Resolved IP Addresses:
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {result.resolved_ips.map((ip: string, i: number) => (
                      <span
                        key={i}
                        className={`px-2 py-0.5 rounded text-xs font-semibold ${
                          result.is_valid
                            ? 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20'
                            : 'bg-rose-500/10 text-rose-300 border border-rose-500/20'
                        }`}
                      >
                        {ip}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Security Rule Explanation */}
              <div className="text-[11px] text-slate-400 pt-1 border-t border-slate-800/40">
                {result.is_valid ? (
                  <span>Verified: Host resolves exclusively to publicly routable internet addresses.</span>
                ) : (
                  <span>
                    Defense in Depth: AWS metadata service (169.254.169.254), RFC1918 private subnets (10/8, 172.16/12, 192.168/16),
                    and loopback interfaces (127.0.0.1) are strictly barred from outgoing probes.
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
