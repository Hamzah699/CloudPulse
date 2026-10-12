import React, { useState, useEffect } from 'react';
import { Plus, Search, Filter, Globe, CheckCircle2 } from 'lucide-react';
import type { Monitor, Stats, AuthUser } from './types';
import { api } from './api/client';

import { Navbar } from './components/Navbar';
import { StatsOverview } from './components/StatsOverview';
import { MonitorCard } from './components/MonitorCard';
import { MonitorModal } from './components/MonitorModal';
import { MonitorDetailModal } from './components/MonitorDetailModal';
import { IncidentList } from './components/IncidentList';
import { LiveCheckerTest } from './components/LiveCheckerTest';
import { NotificationBanner } from './components/NotificationBanner';
import { ArchitectureDiagramModal } from './components/ArchitectureDiagramModal';
import { AuthModal } from './components/AuthModal';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'monitors' | 'incidents' | 'live-check' | 'alerts' | 'architecture'>('monitors');
  const [stats, setStats] = useState<Stats | null>(null);
  const [monitors, setMonitors] = useState<Monitor[]>([]);
  const [loading, setLoading] = useState(true);
  const [checkingAll, setCheckingAll] = useState(false);

  // Search and Filtering
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  // Modals state
  const [isMonitorModalOpen, setIsMonitorModalOpen] = useState(false);
  const [editingMonitor, setEditingMonitor] = useState<Monitor | null>(null);
  const [selectedMonitorForAnalytics, setSelectedMonitorForAnalytics] = useState<Monitor | null>(null);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [user, setUser] = useState<AuthUser | null>(null);

  // Notification / Toast
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 4000);
  };

  const loadData = async (silent: boolean = false) => {
    if (!silent) setLoading(true);
    try {
      const [statsData, monitorsData] = await Promise.all([
        api.getStats().catch(() => null),
        api.getMonitors().catch(() => []),
      ]);
      if (statsData) setStats(statsData);
      setMonitors(monitorsData);
    } catch (err: any) {
      console.error('Failed to load dashboard data:', err);
    } finally {
      if (!silent) setLoading(false);
    }
  };

  useEffect(() => {
    loadData();

    const interval = setInterval(() => {
      loadData(true);
    }, 20000);

    return () => clearInterval(interval);
  }, []);

  const handleSaveMonitor = async (monitorData: Partial<Monitor>) => {
    if (editingMonitor) {
      const updated = await api.updateMonitor(editingMonitor.id, monitorData);
      setMonitors((prev) => prev.map((m) => (m.id === updated.id ? updated : m)));
      showToast(`Updated monitor "${updated.name}"`);
    } else {
      const created = await api.createMonitor(monitorData);
      setMonitors((prev) => [created, ...prev]);
      showToast(`Created monitor "${created.name}" and executed initial health check`);
    }
    await loadData(true);
  };

  const handleCheckNow = async (id: string) => {
    try {
      const res = await api.checkMonitorNow(id);
      setMonitors((prev) => prev.map((m) => (m.id === id ? res.monitor : m)));
      showToast(`Checked "${res.monitor.name}": ${res.check.status} (${Math.round(res.check.latency_ms)}ms)`);
      await loadData(true);
    } catch (err: any) {
      showToast(`Check failed: ${err.message}`);
    }
  };

  const handlePause = async (id: string) => {
    try {
      const updated = await api.pauseMonitor(id);
      setMonitors((prev) => prev.map((m) => (m.id === id ? updated : m)));
      showToast(`Paused monitor "${updated.name}"`);
      await loadData(true);
    } catch (err: any) {
      showToast(`Failed to pause: ${err.message}`);
    }
  };

  const handleResume = async (id: string) => {
    try {
      const updated = await api.resumeMonitor(id);
      setMonitors((prev) => prev.map((m) => (m.id === id ? updated : m)));
      showToast(`Resumed monitor "${updated.name}"`);
      await loadData(true);
    } catch (err: any) {
      showToast(`Failed to resume: ${err.message}`);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await api.deleteMonitor(id);
      setMonitors((prev) => prev.filter((m) => m.id !== id));
      showToast('Monitor deleted successfully');
      await loadData(true);
    } catch (err: any) {
      showToast(`Delete failed: ${err.message}`);
    }
  };

  const handleCheckAll = async () => {
    setCheckingAll(true);
    try {
      const res = await api.checkAllMonitors();
      showToast(`Triggered batch check on ${res.checked_count} active monitors`);
      await loadData(true);
    } catch (err: any) {
      showToast(`Batch check failed: ${err.message}`);
    } finally {
      setCheckingAll(false);
    }
  };

  const filteredMonitors = monitors.filter((m) => {
    const matchesSearch =
      m.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.url.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (m.tags && m.tags.some((t) => t.toLowerCase().includes(searchQuery.toLowerCase())));

    const matchesStatus =
      statusFilter === 'ALL' ||
      m.status === statusFilter;

    return matchesSearch && matchesStatus;
  });

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Toast Notification Banner */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 px-4 py-3 rounded-2xl bg-indigo-600 text-white text-xs font-semibold shadow-2xl shadow-indigo-600/50 flex items-center space-x-2 animate-in slide-in-from-bottom-5 duration-150">
          <CheckCircle2 className="w-4 h-4" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Navigation */}
      <Navbar
        stats={stats}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        user={user}
        onOpenAuth={() => setIsAuthModalOpen(true)}
        onLogout={() => {
          api.logout();
          setUser(null);
          showToast('Signed out of session');
        }}
        onCheckAll={handleCheckAll}
        checkingAll={checkingAll}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* TAB 1: MONITORS DASHBOARD */}
        {activeTab === 'monitors' && (
          <div className="space-y-6">
            {/* Top Telemetry Cards */}
            <StatsOverview stats={stats} loading={loading} />

            {/* Filter Bar & Add Monitor Button */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-2xl bg-slate-900/60 border border-slate-800">
              <div className="flex flex-col sm:flex-row sm:items-center gap-3 flex-1">
                {/* Search Input */}
                <div className="relative flex-1 max-w-md">
                  <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search monitors by name, URL, or tag..."
                    className="w-full pl-9 pr-4 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-xs placeholder:text-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
                  />
                </div>

                {/* Status Dropdown */}
                <div className="flex items-center space-x-2">
                  <Filter className="w-3.5 h-3.5 text-slate-400 hidden sm:block" />
                  <select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                    className="px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-300 focus:outline-none focus:border-indigo-500"
                  >
                    <option value="ALL">All Statuses</option>
                    <option value="UP">Operational (UP)</option>
                    <option value="DOWN">Outage (DOWN)</option>
                    <option value="DEGRADED">Degraded</option>
                    <option value="PAUSED">Paused</option>
                  </select>
                </div>
              </div>

              {/* Add Monitor CTA */}
              <button
                onClick={() => {
                  setEditingMonitor(null);
                  setIsMonitorModalOpen(true);
                }}
                className="px-4 py-2 rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 text-white text-xs font-semibold flex items-center justify-center space-x-1.5 shadow-md shadow-indigo-600/25 transition-all"
              >
                <Plus className="w-4 h-4" />
                <span>Add Monitor</span>
              </button>
            </div>

            {/* Monitors Grid */}
            {loading && monitors.length === 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {[1, 2, 3, 4, 5, 6].map((i) => (
                  <div key={i} className="h-56 rounded-2xl bg-slate-900/40 border border-slate-800 animate-pulse" />
                ))}
              </div>
            ) : filteredMonitors.length === 0 ? (
              <div className="p-16 rounded-2xl bg-slate-900/40 border border-slate-800 text-center">
                <Globe className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                <h3 className="text-base font-semibold text-white">No Monitors Match Criteria</h3>
                <p className="text-xs text-slate-400 max-w-sm mx-auto mt-1 mb-4">
                  {monitors.length === 0
                    ? 'Get started by creating your first serverless website or API uptime health check.'
                    : 'Try clearing your search query or status filter.'}
                </p>
                {monitors.length === 0 && (
                  <button
                    onClick={() => {
                      setEditingMonitor(null);
                      setIsMonitorModalOpen(true);
                    }}
                    className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold inline-flex items-center space-x-1.5"
                  >
                    <Plus className="w-4 h-4" />
                    <span>Create Your First Monitor</span>
                  </button>
                )}
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredMonitors.map((m) => (
                  <MonitorCard
                    key={m.id}
                    monitor={m}
                    onCheckNow={handleCheckNow}
                    onPause={handlePause}
                    onResume={handleResume}
                    onEdit={(mon) => {
                      setEditingMonitor(mon);
                      setIsMonitorModalOpen(true);
                    }}
                    onDelete={handleDelete}
                    onViewAnalytics={(mon) => setSelectedMonitorForAnalytics(mon)}
                  />
                ))}
              </div>
            )}
          </div>
        )}

        {/* TAB 2: INCIDENTS */}
        {activeTab === 'incidents' && <IncidentList />}

        {/* TAB 3: SSRF SANDBOX */}
        {activeTab === 'live-check' && <LiveCheckerTest />}

        {/* TAB 4: SNS ALERTS INBOX */}
        {activeTab === 'alerts' && <NotificationBanner />}

        {/* TAB 5: AWS CLOUD ARCHITECTURE */}
        {activeTab === 'architecture' && <ArchitectureDiagramModal />}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-slate-900/40 py-6 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>CloudPulse — FT-III Cloud Computing Serverless Platform</span>
          <span>AWS SAM • API Gateway • Lambda • DynamoDB • EventBridge • SNS • CloudWatch</span>
        </div>
      </footer>

      {/* Modals */}
      <MonitorModal
        isOpen={isMonitorModalOpen}
        onClose={() => setIsMonitorModalOpen(false)}
        onSave={handleSaveMonitor}
        initialData={editingMonitor}
      />

      <MonitorDetailModal
        isOpen={Boolean(selectedMonitorForAnalytics)}
        onClose={() => setSelectedMonitorForAnalytics(null)}
        monitor={selectedMonitorForAnalytics}
        onCheckNow={handleCheckNow}
      />

      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        onSuccess={(loggedUser) => {
          setUser(loggedUser);
          showToast(`Authenticated as ${loggedUser.email}`);
        }}
      />
    </div>
  );
};

export default App;
