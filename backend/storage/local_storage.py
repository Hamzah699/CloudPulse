"""
Local Storage implementation using SQLite for development without AWS credentials.
Faithfully mirrors DynamoDB behavior and schema definitions.
"""

import sqlite3
import json
import os
import contextlib
from typing import List, Optional, Dict, Any, Generator
from .db_interface import DatabaseInterface
from ..core.models import Monitor, CheckResult, Incident


class LocalStorage(DatabaseInterface):
    def __init__(self, db_path: str = "cloudpulse.db"):
        self.db_path = db_path
        self._init_db()

    @contextlib.contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Monitors table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS monitors (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    url TEXT NOT NULL,
                    method TEXT NOT NULL,
                    interval_seconds INTEGER NOT NULL,
                    timeout_seconds INTEGER NOT NULL,
                    expected_status INTEGER NOT NULL,
                    headers_json TEXT,
                    body TEXT,
                    tags_json TEXT,
                    alert_email TEXT,
                    failure_threshold INTEGER NOT NULL,
                    recovery_threshold INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    consecutive_failures INTEGER NOT NULL,
                    consecutive_successes INTEGER NOT NULL,
                    last_checked_at TEXT,
                    last_status_code INTEGER,
                    last_latency_ms REAL,
                    uptime_percentage REAL NOT NULL,
                    total_checks INTEGER NOT NULL,
                    successful_checks INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    user_id TEXT NOT NULL
                )
            """)

            # Check history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS checks (
                    id TEXT PRIMARY KEY,
                    monitor_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    epoch_timestamp INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    status_code INTEGER,
                    latency_ms REAL NOT NULL,
                    dns_time_ms REAL NOT NULL,
                    connect_time_ms REAL NOT NULL,
                    ttfb_ms REAL NOT NULL,
                    error_message TEXT,
                    target_ip TEXT,
                    checked_from_region TEXT NOT NULL,
                    headers_json TEXT,
                    FOREIGN KEY(monitor_id) REFERENCES monitors(id) ON DELETE CASCADE
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_checks_monitor_time ON checks(monitor_id, timestamp DESC)")

            # Incidents table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS incidents (
                    id TEXT PRIMARY KEY,
                    monitor_id TEXT NOT NULL,
                    monitor_name TEXT NOT NULL,
                    monitor_url TEXT NOT NULL,
                    status TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    resolved_at TEXT,
                    duration_seconds INTEGER,
                    cause TEXT NOT NULL,
                    last_status_code INTEGER,
                    consecutive_failures INTEGER NOT NULL,
                    alert_sent INTEGER NOT NULL,
                    alert_recipient TEXT,
                    acknowledged_by TEXT,
                    acknowledged_at TEXT,
                    user_id TEXT NOT NULL
                )
            """)
            # Notifications table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notifications (
                    id TEXT PRIMARY KEY,
                    subject TEXT NOT NULL,
                    monitor_id TEXT NOT NULL,
                    monitor_name TEXT NOT NULL,
                    monitor_url TEXT NOT NULL,
                    status TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    cause TEXT NOT NULL,
                    recipient TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    duration_seconds INTEGER
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_notifications_time ON notifications(timestamp DESC)")
            conn.commit()

    def save_monitor(self, monitor: Monitor) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO monitors (
                    id, name, url, method, interval_seconds, timeout_seconds, expected_status,
                    headers_json, body, tags_json, alert_email, failure_threshold, recovery_threshold,
                    status, consecutive_failures, consecutive_successes, last_checked_at,
                    last_status_code, last_latency_ms, uptime_percentage, total_checks,
                    successful_checks, created_at, updated_at, user_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name=excluded.name,
                    url=excluded.url,
                    method=excluded.method,
                    interval_seconds=excluded.interval_seconds,
                    timeout_seconds=excluded.timeout_seconds,
                    expected_status=excluded.expected_status,
                    headers_json=excluded.headers_json,
                    body=excluded.body,
                    tags_json=excluded.tags_json,
                    alert_email=excluded.alert_email,
                    failure_threshold=excluded.failure_threshold,
                    recovery_threshold=excluded.recovery_threshold,
                    status=excluded.status,
                    consecutive_failures=excluded.consecutive_failures,
                    consecutive_successes=excluded.consecutive_successes,
                    last_checked_at=excluded.last_checked_at,
                    last_status_code=excluded.last_status_code,
                    last_latency_ms=excluded.last_latency_ms,
                    uptime_percentage=excluded.uptime_percentage,
                    total_checks=excluded.total_checks,
                    successful_checks=excluded.successful_checks,
                    updated_at=excluded.updated_at
            """, (
                monitor.id, monitor.name, monitor.url, monitor.method, monitor.interval_seconds,
                monitor.timeout_seconds, monitor.expected_status, json.dumps(monitor.headers or {}),
                monitor.body, json.dumps(monitor.tags or []), monitor.alert_email,
                monitor.failure_threshold, monitor.recovery_threshold, monitor.status,
                monitor.consecutive_failures, monitor.consecutive_successes, monitor.last_checked_at,
                monitor.last_status_code, monitor.last_latency_ms, monitor.uptime_percentage,
                monitor.total_checks, monitor.successful_checks, monitor.created_at,
                monitor.updated_at, monitor.user_id
            ))
            conn.commit()

    def get_monitor(self, monitor_id: str) -> Optional[Monitor]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM monitors WHERE id = ?", (monitor_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_monitor(row)

    def list_monitors(self, user_id: Optional[str] = None) -> List[Monitor]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if user_id:
                cursor.execute("SELECT * FROM monitors WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
            else:
                cursor.execute("SELECT * FROM monitors ORDER BY created_at DESC")
            rows = cursor.fetchall()
            return [self._row_to_monitor(r) for r in rows]

    def delete_monitor(self, monitor_id: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM monitors WHERE id = ?", (monitor_id,))
            mon_deleted = cursor.rowcount > 0
            cursor.execute("DELETE FROM checks WHERE monitor_id = ?", (monitor_id,))
            cursor.execute("DELETE FROM incidents WHERE monitor_id = ?", (monitor_id,))
            conn.commit()
            return mon_deleted

    def save_check(self, check: CheckResult) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO checks (
                    id, monitor_id, timestamp, epoch_timestamp, status, status_code,
                    latency_ms, dns_time_ms, connect_time_ms, ttfb_ms, error_message,
                    target_ip, checked_from_region, headers_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                check.id, check.monitor_id, check.timestamp, check.epoch_timestamp,
                check.status, check.status_code, check.latency_ms, check.dns_time_ms,
                check.connect_time_ms, check.ttfb_ms, check.error_message,
                check.target_ip, check.checked_from_region, json.dumps(check.headers or {})
            ))
            conn.commit()

    def get_checks(self, monitor_id: str, limit: int = 50) -> List[CheckResult]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM checks WHERE monitor_id = ? ORDER BY timestamp DESC LIMIT ?
            """, (monitor_id, limit))
            rows = cursor.fetchall()
            return [self._row_to_check(r) for r in rows]

    def save_incident(self, incident: Incident) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO incidents (
                    id, monitor_id, monitor_name, monitor_url, status, started_at,
                    resolved_at, duration_seconds, cause, last_status_code,
                    consecutive_failures, alert_sent, alert_recipient,
                    acknowledged_by, acknowledged_at, user_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    status=excluded.status,
                    resolved_at=excluded.resolved_at,
                    duration_seconds=excluded.duration_seconds,
                    cause=excluded.cause,
                    last_status_code=excluded.last_status_code,
                    consecutive_failures=excluded.consecutive_failures,
                    alert_sent=excluded.alert_sent,
                    alert_recipient=excluded.alert_recipient,
                    acknowledged_by=excluded.acknowledged_by,
                    acknowledged_at=excluded.acknowledged_at
            """, (
                incident.id, incident.monitor_id, incident.monitor_name, incident.monitor_url,
                incident.status, incident.started_at, incident.resolved_at, incident.duration_seconds,
                incident.cause, incident.last_status_code, incident.consecutive_failures,
                1 if incident.alert_sent else 0, incident.alert_recipient,
                incident.acknowledged_by, incident.acknowledged_at, incident.user_id
            ))
            conn.commit()

    def get_incident(self, incident_id: str) -> Optional[Incident]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_incident(row)

    def list_incidents(self, monitor_id: Optional[str] = None, status: Optional[str] = None) -> List[Incident]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM incidents WHERE 1=1"
            params = []
            if monitor_id:
                query += " AND monitor_id = ?"
                params.append(monitor_id)
            if status:
                query += " AND status = ?"
                params.append(status)
            query += " ORDER BY started_at DESC"
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [self._row_to_incident(r) for r in rows]

    def save_notification(self, notif: Dict[str, Any]) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO notifications (
                    id, subject, monitor_id, monitor_name, monitor_url, status,
                    event_type, cause, recipient, timestamp, duration_seconds
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    subject=excluded.subject,
                    status=excluded.status,
                    event_type=excluded.event_type,
                    cause=excluded.cause
            """, (
                notif.get("id"), notif.get("subject"), notif.get("monitor_id"),
                notif.get("monitor_name"), notif.get("monitor_url"), notif.get("status"),
                notif.get("event_type"), notif.get("cause"), notif.get("recipient"),
                notif.get("timestamp"), notif.get("duration_seconds")
            ))
            conn.commit()

    def get_notifications(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM notifications ORDER BY timestamp DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def get_active_incident(self, monitor_id: str) -> Optional[Incident]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM incidents WHERE monitor_id = ? AND status IN ('OPEN', 'ACKNOWLEDGED')
                ORDER BY started_at DESC LIMIT 1
            """, (monitor_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_incident(row)

    def get_summary_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        monitors = self.list_monitors(user_id=user_id)
        total = len(monitors)
        up_count = sum(1 for m in monitors if m.status == "UP")
        down_count = sum(1 for m in monitors if m.status == "DOWN")
        degraded_count = sum(1 for m in monitors if m.status == "DEGRADED")
        paused_count = sum(1 for m in monitors if m.status == "PAUSED")
        pending_count = sum(1 for m in monitors if m.status == "PENDING")

        avg_uptime = (sum(m.uptime_percentage for m in monitors) / total) if total > 0 else 100.0
        active_latencies = [m.last_latency_ms for m in monitors if m.last_latency_ms is not None and m.last_latency_ms > 0]
        avg_latency = (sum(active_latencies) / len(active_latencies)) if active_latencies else 0.0

        open_incidents = len(self.list_incidents(status="OPEN"))

        return {
            "total_monitors": total,
            "up_count": up_count,
            "down_count": down_count,
            "degraded_count": degraded_count,
            "paused_count": paused_count,
            "pending_count": pending_count,
            "overall_uptime_percentage": round(avg_uptime, 2),
            "average_latency_ms": round(avg_latency, 2),
            "open_incidents_count": open_incidents
        }

    # Helpers
    def _row_to_monitor(self, row: sqlite3.Row) -> Monitor:
        return Monitor(
            id=row["id"],
            name=row["name"],
            url=row["url"],
            method=row["method"],
            interval_seconds=row["interval_seconds"],
            timeout_seconds=row["timeout_seconds"],
            expected_status=row["expected_status"],
            headers=json.loads(row["headers_json"] or "{}"),
            body=row["body"],
            tags=json.loads(row["tags_json"] or "[]"),
            alert_email=row["alert_email"],
            failure_threshold=row["failure_threshold"],
            recovery_threshold=row["recovery_threshold"],
            status=row["status"],
            consecutive_failures=row["consecutive_failures"],
            consecutive_successes=row["consecutive_successes"],
            last_checked_at=row["last_checked_at"],
            last_status_code=row["last_status_code"],
            last_latency_ms=row["last_latency_ms"],
            uptime_percentage=row["uptime_percentage"],
            total_checks=row["total_checks"],
            successful_checks=row["successful_checks"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            user_id=row["user_id"]
        )

    def _row_to_check(self, row: sqlite3.Row) -> CheckResult:
        return CheckResult(
            id=row["id"],
            monitor_id=row["monitor_id"],
            timestamp=row["timestamp"],
            epoch_timestamp=row["epoch_timestamp"],
            status=row["status"],
            status_code=row["status_code"],
            latency_ms=row["latency_ms"],
            dns_time_ms=row["dns_time_ms"],
            connect_time_ms=row["connect_time_ms"],
            ttfb_ms=row["ttfb_ms"],
            error_message=row["error_message"],
            target_ip=row["target_ip"],
            checked_from_region=row["checked_from_region"],
            headers=json.loads(row["headers_json"] or "{}")
        )

    def _row_to_incident(self, row: sqlite3.Row) -> Incident:
        return Incident(
            id=row["id"],
            monitor_id=row["monitor_id"],
            monitor_name=row["monitor_name"],
            monitor_url=row["monitor_url"],
            status=row["status"],
            started_at=row["started_at"],
            resolved_at=row["resolved_at"],
            duration_seconds=row["duration_seconds"],
            cause=row["cause"],
            last_status_code=row["last_status_code"],
            consecutive_failures=row["consecutive_failures"],
            alert_sent=bool(row["alert_sent"]),
            alert_recipient=row["alert_recipient"],
            acknowledged_by=row["acknowledged_by"],
            acknowledged_at=row["acknowledged_at"],
            user_id=row["user_id"]
        )
