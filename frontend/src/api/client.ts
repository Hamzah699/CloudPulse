import type { Monitor, CheckResult, Incident, Stats, NotificationItem, AuthUser } from '../types';

const BASE_URL = import.meta.env.VITE_API_URL || '';

class ApiClient {
  private token: string | null = null;

  constructor() {
    this.token = localStorage.getItem('cloudpulse_token');
  }

  setToken(token: string | null) {
    this.token = token;
    if (token) {
      localStorage.setItem('cloudpulse_token', token);
    } else {
      localStorage.removeItem('cloudpulse_token');
    }
  }

  getToken(): string | null {
    return this.token;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${BASE_URL}${endpoint}`;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      let errMsg = `HTTP Error ${response.status}: ${response.statusText}`;
      try {
        const errData = await response.json();
        if (errData && errData.error) {
          errMsg = errData.error;
        }
      } catch {
        // Fall back to status text
      }
      throw new Error(errMsg);
    }

    return response.json();
  }

  // Authentication
  async login(email: string): Promise<AuthUser> {
    const data = await this.request<{ token: string; user: { id: string; email: string; role: string } }>(
      '/api/auth/login',
      {
        method: 'POST',
        body: JSON.stringify({ email }),
      }
    );
    this.setToken(data.token);
    return { ...data.user, token: data.token };
  }

  async register(email: string): Promise<AuthUser> {
    const data = await this.request<{ token: string; user: { id: string; email: string; role: string } }>(
      '/api/auth/register',
      {
        method: 'POST',
        body: JSON.stringify({ email }),
      }
    );
    this.setToken(data.token);
    return { ...data.user, token: data.token };
  }

  logout() {
    this.setToken(null);
  }

  // Statistics
  async getStats(): Promise<Stats> {
    return this.request<Stats>('/api/stats');
  }

  // Monitors
  async getMonitors(): Promise<Monitor[]> {
    return this.request<Monitor[]>('/api/monitors');
  }

  async getMonitor(id: string): Promise<Monitor> {
    return this.request<Monitor>(`/api/monitors/${id}`);
  }

  async createMonitor(data: Partial<Monitor>): Promise<Monitor> {
    return this.request<Monitor>('/api/monitors', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async updateMonitor(id: string, data: Partial<Monitor>): Promise<Monitor> {
    return this.request<Monitor>(`/api/monitors/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async deleteMonitor(id: string): Promise<{ message: string; id: string }> {
    return this.request<{ message: string; id: string }>(`/api/monitors/${id}`, {
      method: 'DELETE',
    });
  }

  async pauseMonitor(id: string): Promise<Monitor> {
    return this.request<Monitor>(`/api/monitors/${id}/pause`, {
      method: 'POST',
    });
  }

  async resumeMonitor(id: string): Promise<Monitor> {
    return this.request<Monitor>(`/api/monitors/${id}/resume`, {
      method: 'POST',
    });
  }

  async checkMonitorNow(id: string): Promise<{ check: CheckResult; monitor: Monitor; incident?: Incident; event_type: string }> {
    return this.request<{ check: CheckResult; monitor: Monitor; incident?: Incident; event_type: string }>(
      `/api/monitors/${id}/check`,
      {
        method: 'POST',
      }
    );
  }

  async checkAllMonitors(): Promise<{ checked_count: number; results: any[] }> {
    return this.request<{ checked_count: number; results: any[] }>('/api/monitors/check-all', {
      method: 'POST',
    });
  }

  // Check History
  async getChecks(monitorId: string, limit: number = 30): Promise<CheckResult[]> {
    return this.request<CheckResult[]>(`/api/monitors/${monitorId}/checks?limit=${limit}`);
  }

  // Incidents
  async getIncidents(status?: string): Promise<Incident[]> {
    const query = status ? `?status=${status}` : '';
    return this.request<Incident[]>(`/api/incidents${query}`);
  }

  async acknowledgeIncident(id: string): Promise<Incident> {
    return this.request<Incident>(`/api/incidents/${id}/acknowledge`, {
      method: 'POST',
    });
  }

  // Notifications
  async getNotifications(): Promise<NotificationItem[]> {
    return this.request<NotificationItem[]>('/api/notifications');
  }

  // SSRF Validator Tool
  async validateUrlSSRF(url: string): Promise<{ url: string; is_valid: boolean; error?: string; resolved_ips: string[] }> {
    return this.request<{ url: string; is_valid: boolean; error?: string; resolved_ips: string[] }>(
      '/api/tools/validate-url',
      {
        method: 'POST',
        body: JSON.stringify({ url }),
      }
    );
  }
}

export const api = new ApiClient();
