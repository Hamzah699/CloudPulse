export interface Monitor {
  id: string;
  name: string;
  url: string;
  method: string;
  interval_seconds: number;
  timeout_seconds: number;
  expected_status: number;
  headers?: Record<string, string>;
  body?: string | null;
  tags?: string[];
  alert_email?: string | null;
  failure_threshold: number;
  recovery_threshold: number;
  status: 'UP' | 'DOWN' | 'PAUSED' | 'DEGRADED' | 'PENDING';
  consecutive_failures: number;
  consecutive_successes: number;
  last_checked_at?: string | null;
  last_status_code?: number | null;
  last_latency_ms?: number | null;
  uptime_percentage: number;
  total_checks: number;
  successful_checks: number;
  created_at: string;
  updated_at: string;
  user_id?: string;
}

export interface CheckResult {
  id: string;
  monitor_id: string;
  timestamp: string;
  epoch_timestamp: number;
  status: 'UP' | 'DOWN';
  status_code?: number | null;
  latency_ms: number;
  dns_time_ms: number;
  connect_time_ms: number;
  ttfb_ms: number;
  error_message?: string | null;
  target_ip?: string | null;
  checked_from_region: string;
  headers?: Record<string, string>;
}

export interface Incident {
  id: string;
  monitor_id: string;
  monitor_name: string;
  monitor_url: string;
  status: 'OPEN' | 'ACKNOWLEDGED' | 'RESOLVED';
  started_at: string;
  resolved_at?: string | null;
  duration_seconds?: number | null;
  cause: string;
  last_status_code?: number | null;
  consecutive_failures: number;
  alert_sent: boolean;
  alert_recipient?: string | null;
  acknowledged_by?: string | null;
  acknowledged_at?: string | null;
  user_id?: string;
}

export interface Stats {
  total_monitors: number;
  up_count: number;
  down_count: number;
  degraded_count: number;
  paused_count: number;
  pending_count: number;
  overall_uptime_percentage: number;
  average_latency_ms: number;
  open_incidents_count: number;
}

export interface NotificationItem {
  id: string;
  subject: string;
  monitor_id: string;
  monitor_name: string;
  monitor_url: string;
  status: string;
  event_type: string;
  cause: string;
  recipient: string;
  timestamp: string;
  duration_seconds?: number | null;
}

export interface AuthUser {
  id: string;
  email: string;
  role: string;
  token: string;
}
