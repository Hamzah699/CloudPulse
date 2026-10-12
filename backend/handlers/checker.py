"""
EventBridge Scheduled Lambda Handler for CloudPulse.
Invoked periodically (e.g. rate(1 minute)) by Amazon EventBridge Scheduler.
Executes HTTP health checks for active monitors, records metrics in DynamoDB,
evaluates incident state transitions, and triggers SNS notifications on outages or recovery.
"""

import os
import json
import time
from typing import Dict, Any, List

from ..core.models import Monitor, CheckResult, Incident
from ..core.http_checker import perform_health_check
from ..core.incident_engine import process_check_result, IncidentEventType
from ..storage import get_storage
from ..notify.notifier import get_notifier


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Scheduled Lambda entrypoint for health check automation.
    """
    start_time = time.time()
    region = os.environ.get("AWS_REGION", "us-east-1")
    print(f"[CloudPulse HealthChecker] Invocation started at {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")

    storage = get_storage()
    notifier = get_notifier()

    # Retrieve all configured monitors
    all_monitors = storage.list_monitors()
    active_monitors = [m for m in all_monitors if m.status != "PAUSED"]

    print(f"[CloudPulse HealthChecker] Found {len(all_monitors)} total monitors ({len(active_monitors)} active)")

    results: List[Dict[str, Any]] = []
    up_count = 0
    down_count = 0
    alerts_dispatched = 0

    for monitor in active_monitors:
        try:
            # 1. Execute real HTTP probe with SSRF protection
            check = perform_health_check(monitor, region=region)
            
            # 2. Retrieve any active incident for this monitor
            active_incident = storage.get_active_incident(monitor.id)

            # 3. Process state machine transition
            updated_monitor, resulting_incident, event_type = process_check_result(
                monitor, check, active_incident
            )

            # 4. Save results to persistence (DynamoDB in cloud, SQLite locally)
            storage.save_check(check)
            storage.save_monitor(updated_monitor)
            if resulting_incident:
                storage.save_incident(resulting_incident)

            # 5. Dispatch notification if incident state changed
            if event_type in (IncidentEventType.INCIDENT_OPENED, IncidentEventType.INCIDENT_RESOLVED):
                try:
                    sent = notifier.send_incident_alert(resulting_incident, updated_monitor, event_type)
                    if sent and resulting_incident:
                        resulting_incident.alert_sent = True
                        storage.save_incident(resulting_incident)
                    alerts_dispatched += 1
                    print(f"[CloudPulse Alert] Sent notification for {monitor.name} (Event: {event_type})")
                except Exception as alert_err:
                    print(f"[CloudPulse Alert Error] Failed to send notification: {alert_err}")

            if check.status == "UP":
                up_count += 1
            else:
                down_count += 1

            results.append({
                "id": monitor.id,
                "name": monitor.name,
                "status": check.status,
                "latency_ms": check.latency_ms,
                "status_code": check.status_code,
                "event_type": event_type
            })

        except Exception as e:
            print(f"[CloudPulse Error] Exception checking monitor {monitor.id} ({monitor.name}): {e}")
            down_count += 1

    duration = round(time.time() - start_time, 2)
    summary = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "monitors_checked": len(results),
        "up": up_count,
        "down": down_count,
        "alerts_dispatched": alerts_dispatched,
        "execution_duration_seconds": duration
    }

    # Structured CloudWatch log line
    print(f"[CloudPulse Metrics] {json.dumps(summary)}")
    return summary


if __name__ == "__main__":
    # Test execution when run as standalone script
    handler({}, None)
