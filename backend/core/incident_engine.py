"""
Incident Management Engine for CloudPulse.
State machine for tracking consecutive failures, opening incidents when thresholds are crossed,
and auto-resolving incidents upon sustained recovery.
"""

from typing import Tuple, Optional, Dict, Any
import time
from .models import Monitor, CheckResult, Incident


class IncidentEventType:
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    INCIDENT_OPENED = "INCIDENT_OPENED"
    INCIDENT_ONGOING = "INCIDENT_ONGOING"
    RECOVERING = "RECOVERING"
    INCIDENT_RESOLVED = "INCIDENT_RESOLVED"


def process_check_result(
    monitor: Monitor,
    check: CheckResult,
    active_incident: Optional[Incident] = None
) -> Tuple[Monitor, Optional[Incident], str]:
    """
    Evaluates check result against monitor thresholds and existing incident state.
    
    Returns:
        (updated_monitor: Monitor, incident_state: Optional[Incident], event_type: str)
    """
    event_type = IncidentEventType.HEALTHY
    resulting_incident = active_incident

    # Update aggregate totals
    monitor.total_checks += 1
    if check.status == "UP":
        monitor.successful_checks += 1

    monitor.uptime_percentage = round((monitor.successful_checks / monitor.total_checks) * 100, 2)
    monitor.last_checked_at = check.timestamp
    monitor.last_status_code = check.status_code
    monitor.last_latency_ms = check.latency_ms
    monitor.updated_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    # Branch 1: Check failed (DOWN)
    if check.status == "DOWN":
        monitor.consecutive_failures += 1
        monitor.consecutive_successes = 0

        # Check threshold
        if monitor.consecutive_failures >= monitor.failure_threshold:
            if not active_incident or active_incident.status == "RESOLVED":
                # Create a new Incident
                resulting_incident = Incident(
                    monitor_id=monitor.id,
                    monitor_name=monitor.name,
                    monitor_url=monitor.url,
                    status="OPEN",
                    started_at=check.timestamp,
                    cause=check.error_message or "Health check returned error",
                    last_status_code=check.status_code,
                    consecutive_failures=monitor.consecutive_failures,
                    alert_recipient=monitor.alert_email,
                    user_id=monitor.user_id
                )
                monitor.status = "DOWN"
                event_type = IncidentEventType.INCIDENT_OPENED
            else:
                # Update existing open incident
                resulting_incident.consecutive_failures = monitor.consecutive_failures
                resulting_incident.last_status_code = check.status_code
                resulting_incident.cause = check.error_message or resulting_incident.cause
                monitor.status = "DOWN"
                event_type = IncidentEventType.INCIDENT_ONGOING
        else:
            # Failed, but below threshold
            monitor.status = "DEGRADED"
            event_type = IncidentEventType.DEGRADED

    # Branch 2: Check succeeded (UP)
    else:
        monitor.consecutive_successes += 1
        monitor.consecutive_failures = 0

        if active_incident and active_incident.status in ("OPEN", "ACKNOWLEDGED"):
            # Check if recovery threshold reached
            if monitor.consecutive_successes >= monitor.recovery_threshold:
                # Auto-resolve incident
                resulting_incident.status = "RESOLVED"
                resulting_incident.resolved_at = check.timestamp
                
                # Compute duration
                try:
                    start_epoch = time.mktime(time.strptime(resulting_incident.started_at, "%Y-%m-%dT%H:%M:%SZ"))
                    resolve_epoch = time.mktime(time.strptime(check.timestamp, "%Y-%m-%dT%H:%M:%SZ"))
                    resulting_incident.duration_seconds = max(0, int(resolve_epoch - start_epoch))
                except Exception:
                    resulting_incident.duration_seconds = 0

                monitor.status = "UP"
                event_type = IncidentEventType.INCIDENT_RESOLVED
            else:
                # Waiting for additional consecutive passes
                monitor.status = "DEGRADED"
                event_type = IncidentEventType.RECOVERING
        else:
            monitor.status = "UP"
            event_type = IncidentEventType.HEALTHY

    return monitor, resulting_incident, event_type
