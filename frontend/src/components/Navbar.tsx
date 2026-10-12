import React from 'react';
import { Activity, Bell, RefreshCw, Server, LogIn, LogOut, CheckCircle2, AlertOctagon } from 'lucide-react';
import type { Stats, AuthUser } from '../types';

interface NavbarProps {
  stats: Stats | null;
  activeTab: 'monitors' | 'incidents' | 'live-check' | 'alerts' | 'architecture';
  setActiveTab: (tab: 'monitors' | 'incidents' | 'live-check' | 'alerts' | 'architecture') => void;
  user: AuthUser | null;
  onOpenAuth: () => void;
  onLogout: () => void;
  onCheckAll: () => void;
  checkingAll: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  stats,
  activeTab,
  setActiveTab,
  user,
  onOpenAuth,
  onLogout,
  onCheckAll,
  checkingAll,
}) => {
  const isHealthy = !stats || stats.open_incidents_count === 0;

  return (
    <header className="sticky top-0 z-40 bg-slate-900/90 backdrop-blur-md border-b border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand Logo */}
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setActiveTab('monitors')}>
            <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-cyan-500 shadow-lg shadow-indigo-500/25">
              <Activity className="w-5 h-5 text-white animate-pulse" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-xl font-bold tracking-tight text-white">CloudPulse</span>
                <span className="px-1.5 py-0.5 text-[10px] font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 rounded">
                  SERVERLESS
                </span>
              </div>
              <p className="text-xs text-slate-400">AWS Uptime & Incident Platform</p>
            </div>
          </div>

          {/* System Status Pill */}
          <div className="hidden md:flex items-center">
            {isHealthy ? (
              <div className="flex items-center space-x-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-medium">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>All Systems Operational</span>
              </div>
            ) : (
              <div className="flex items-center space-x-2 px-3 py-1 rounded-full bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs font-medium animate-pulse">
                <AlertOctagon className="w-3.5 h-3.5" />
                <span>{stats?.open_incidents_count} Active Incident{stats?.open_incidents_count !== 1 ? 's' : ''}</span>
              </div>
            )}
          </div>

          {/* Navigation Links */}
          <nav className="flex items-center space-x-1 sm:space-x-2">
            <button
              onClick={() => setActiveTab('monitors')}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                activeTab === 'monitors'
                  ? 'bg-slate-800 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              Monitors
            </button>

            <button
              onClick={() => setActiveTab('incidents')}
              className={`relative px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                activeTab === 'incidents'
                  ? 'bg-slate-800 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              <span>Incidents</span>
              {stats && stats.open_incidents_count > 0 && (
                <span className="ml-1.5 px-1.5 py-0.2 text-[11px] font-bold bg-rose-500 text-white rounded-full">
                  {stats.open_incidents_count}
                </span>
              )}
            </button>

            <button
              onClick={() => setActiveTab('live-check')}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                activeTab === 'live-check'
                  ? 'bg-slate-800 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
            >
              SSRF Sandbox
            </button>

            <button
              onClick={() => setActiveTab('alerts')}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                activeTab === 'alerts'
                  ? 'bg-slate-800 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
              title="SNS Alerts Inbox"
            >
              <Bell className="w-4 h-4 inline mr-1" />
              <span>Alerts</span>
            </button>

            <button
              onClick={() => setActiveTab('architecture')}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                activeTab === 'architecture'
                  ? 'bg-slate-800 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
              }`}
              title="AWS Serverless Architecture & Viva Guide"
            >
              <Server className="w-4 h-4 inline mr-1 text-cyan-400" />
              <span>AWS Cloud</span>
            </button>
          </nav>

          {/* Quick Action & Auth */}
          <div className="flex items-center space-x-3">
            <button
              onClick={onCheckAll}
              disabled={checkingAll}
              className="hidden sm:inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 hover:bg-indigo-600/30 text-xs font-medium transition-colors disabled:opacity-50"
              title="Trigger EventBridge health check execution immediately"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${checkingAll ? 'animate-spin' : ''}`} />
              <span>{checkingAll ? 'Checking...' : 'Check All'}</span>
            </button>

            {user ? (
              <div className="flex items-center space-x-2">
                <div className="hidden lg:block text-right">
                  <p className="text-xs font-medium text-slate-200 truncate max-w-[120px]">{user.email}</p>
                  <p className="text-[10px] text-emerald-400 font-mono">Cognito Auth</p>
                </div>
                <button
                  onClick={onLogout}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition-colors"
                  title="Sign Out"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <button
                onClick={onOpenAuth}
                className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition-colors"
              >
                <LogIn className="w-3.5 h-3.5" />
                <span>Sign In</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
