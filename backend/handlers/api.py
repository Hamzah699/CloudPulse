"""
API Gateway Lambda Handler for CloudPulse.
Routes CRUD operations for monitors, health check runs, incidents, statistics, and SSRF pre-validation.
"""

import json
import re
from typing import Dict, Any, Optional

from ..core.models import Monitor, CheckResult, Incident
from ..core.ssrf_guard import validate_target_url
from ..core.http_checker import perform_health_check
from ..core.incident_engine import process_check_result, IncidentEventType
from ..core.auth import get_authenticated_user, generate_local_token
from ..storage import get_storage
from ..notify.notifier import get_notifier, LocalNotifier


def build_response(status_code: int, body: Any, cors: bool = True) -> Dict[str, Any]:
    """Generates a standard API Gateway response with CORS headers."""
    headers = {
        "Content-Type": "application/json",
    }
    if cors:
        headers.update({
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS,PATCH"
        })

    return {
        "statusCode": status_code,
        "headers": headers,
        "body": json.dumps(body) if not isinstance(body, str) else body
    }


def parse_body(event: Dict[str, Any]) -> Dict[str, Any]:
    """Extracts and parses JSON request body."""
    raw_body = event.get("body")
    if not raw_body:
        return {}
    if isinstance(raw_body, dict):
        return raw_body
    try:
        return json.loads(raw_body)
    except Exception:
        return {}


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Main Lambda routing function for API Gateway requests."""
    # Handle API Gateway HTTP API v2 ($context.http.method) or REST API v1 (httpMethod)
    http_method = event.get("httpMethod") or event.get("requestContext", {}).get("http", {}).get("method", "GET")
    path = event.get("path") or event.get("rawPath") or "/"
    
    # Preflight CORS check
    if http_method.upper() == "OPTIONS":
        return build_response(200, {"message": "CORS preflight OK"})

    storage = get_storage()
    headers = event.get("headers") or {}

    # Public Routes
    if path == "/health" or path == "/api/health":
        return build_response(200, {
            "status": "healthy",
            "service": "CloudPulse API",
            "timestamp": event.get("requestContext", {}).get("timeEpoch")
        })

    # Public Auth endpoints (Local simulation & authentication helper)
    if path == "/api/auth/login" and http_method.upper() == "POST":
        body = parse_body(event)
        email = body.get("email", "admin@cloudpulse.io")
        user_id = f"user_{abs(hash(email)) % 100000}"
        token = generate_local_token(user_id=user_id, email=email)
        return build_response(200, {
            "token": token,
            "user": {"id": user_id, "email": email, "role": "admin"}
        })

    if path == "/api/auth/register" and http_method.upper() == "POST":
        body = parse_body(event)
        email = body.get("email", "newuser@cloudpulse.io")
        user_id = f"user_{abs(hash(email)) % 100000}"
        token = generate_local_token(user_id=user_id, email=email)
        return build_response(201, {
            "token": token,
            "user": {"id": user_id, "email": email, "role": "admin"}
        })

    # SSRF Pre-validation utility (allows UI to test URLs live with immediate security feedback)
    if path == "/api/tools/validate-url" and http_method.upper() == "POST":
        body = parse_body(event)
        target_url = body.get("url", "")
        is_valid, err_msg, resolved_ips = validate_target_url(target_url)
        return build_response(200, {
            "url": target_url,
            "is_valid": is_valid,
            "error": err_msg if not is_valid else None,
            "resolved_ips": resolved_ips
        })

    # Authenticate all other routes
    is_auth, user_claims, auth_err = get_authenticated_user(headers, event.get("requestContext"))
    if not is_auth:
        return build_response(401, {"error": f"Unauthorized: {auth_err}"})

    user_id = user_claims.get("user_id", "default_user")

    # -------------------------------------------------------------
    # 1. Summary Statistics Route
    # -------------------------------------------------------------
    if path == "/api/stats" and http_method.upper() == "GET":
        stats = storage.get_summary_stats(user_id=user_id)
        if stats.get("total_monitors", 0) == 0:
            stats = storage.get_summary_stats(user_id=None)
        return build_response(200, stats)

    # -------------------------------------------------------------
    # 2. Notifications Route (Recent alert logs)
    # -------------------------------------------------------------
    if path == "/api/notifications" and http_method.upper() == "GET":
        notifications = LocalNotifier.get_notifications()
        return build_response(200, notifications)

    # -------------------------------------------------------------
    # 3. Incidents Routes
    # -------------------------------------------------------------
    if path == "/api/incidents" and http_method.upper() == "GET":
        status_filter = (event.get("queryStringParameters") or {}).get("status")
        incidents = storage.list_incidents(status=status_filter)
        return build_response(200, [inc.to_dict() for inc in incidents])

    match_ack = re.match(r"^/api/incidents/([^/]+)/acknowledge$", path)
    if match_ack and http_method.upper() == "POST":
        inc_id = match_ack.group(1)
        inc = storage.get_incident(inc_id)
        if not inc:
            return build_response(404, {"error": "Incident not found"})
        inc.status = "ACKNOWLEDGED"
        inc.acknowledged_by = user_claims.get("email", user_id)
        storage.save_incident(inc)
        return build_response(200, inc.to_dict())

    # -------------------------------------------------------------
    # 4. Check All Monitors Route (Manual bulk trigger)
    # -------------------------------------------------------------
    if path == "/api/monitors/check-all" and http_method.upper() == "POST":
        monitors = storage.list_monitors(user_id=user_id)
        results = []
        notifier = get_notifier()

        for mon in monitors:
            if mon.status == "PAUSED":
                continue
            check = perform_health_check(mon)
            active_inc = storage.get_active_incident(mon.id)
            updated_mon, resulting_inc, event_type = process_check_result(mon, check, active_inc)

            storage.save_check(check)
            storage.save_monitor(updated_mon)
            if resulting_inc:
                storage.save_incident(resulting_inc)

            if event_type in (IncidentEventType.INCIDENT_OPENED, IncidentEventType.INCIDENT_RESOLVED):
                try:
                    notifier.send_incident_alert(resulting_inc, updated_mon, event_type)
                    if resulting_inc:
                        resulting_inc.alert_sent = True
                        storage.save_incident(resulting_inc)
                except Exception as e:
                    print(f"Failed to send notification: {e}")

            results.append({
                "monitor_id": mon.id,
                "status": check.status,
                "latency_ms": check.latency_ms,
                "status_code": check.status_code,
                "event_type": event_type
            })

        return build_response(200, {"checked_count": len(results), "results": results})

    # -------------------------------------------------------------
    # 5. Monitors Collection Routes
    # -------------------------------------------------------------
    if path == "/api/monitors" and http_method.upper() == "GET":
        monitors = storage.list_monitors(user_id=user_id)
        if not monitors:
            monitors = storage.list_monitors(user_id=None)
        return build_response(200, [m.to_dict() for m in monitors])

    if path == "/api/monitors" and http_method.upper() == "POST":
        body = parse_body(event)
        name = (body.get("name") or "").strip()
        url = (body.get("url") or "").strip()

        if not name:
            return build_response(400, {"error": "Monitor name is required"})
        if not url:
            return build_response(400, {"error": "Target URL is required"})

        # SSRF validation
        is_valid, err_msg, _ = validate_target_url(url)
        if not is_valid:
            return build_response(400, {"error": f"Invalid target URL: {err_msg}"})

        monitor = Monitor(
            name=name,
            url=url,
            method=(body.get("method") or "GET").upper(),
            interval_seconds=int(body.get("interval_seconds") or 60),
            timeout_seconds=int(body.get("timeout_seconds") or 10),
            expected_status=int(body.get("expected_status") or 200),
            headers=body.get("headers") or {},
            body=body.get("body"),
            tags=body.get("tags") or [],
            alert_email=body.get("alert_email"),
            failure_threshold=int(body.get("failure_threshold") or 2),
            recovery_threshold=int(body.get("recovery_threshold") or 2),
            user_id=user_id
        )

        storage.save_monitor(monitor)

        # Immediately execute initial health check so dashboard has instant data
        check = perform_health_check(monitor)
        updated_mon, _, _ = process_check_result(monitor, check)
        storage.save_check(check)
        storage.save_monitor(updated_mon)

        return build_response(201, updated_mon.to_dict())

    # -------------------------------------------------------------
    # 6. Single Monitor Routes (/api/monitors/{id}...)
    # -------------------------------------------------------------
    match_check_now = re.match(r"^/api/monitors/([^/]+)/check$", path)
    if match_check_now and http_method.upper() == "POST":
        mon_id = match_check_now.group(1)
        mon = storage.get_monitor(mon_id)
        if not mon:
            return build_response(404, {"error": "Monitor not found"})

        check = perform_health_check(mon)
        active_inc = storage.get_active_incident(mon.id)
        updated_mon, resulting_inc, event_type = process_check_result(mon, check, active_inc)

        storage.save_check(check)
        storage.save_monitor(updated_mon)
        if resulting_inc:
            storage.save_incident(resulting_inc)

        if event_type in (IncidentEventType.INCIDENT_OPENED, IncidentEventType.INCIDENT_RESOLVED):
            try:
                notifier = get_notifier()
                notifier.send_incident_alert(resulting_inc, updated_mon, event_type)
                if resulting_inc:
                    resulting_inc.alert_sent = True
                    storage.save_incident(resulting_inc)
            except Exception as e:
                print(f"Failed to dispatch alert: {e}")

        return build_response(200, {
            "check": check.to_dict(),
            "monitor": updated_mon.to_dict(),
            "incident": resulting_inc.to_dict() if resulting_inc else None,
            "event_type": event_type
        })

    match_checks = re.match(r"^/api/monitors/([^/]+)/checks$", path)
    if match_checks and http_method.upper() == "GET":
        mon_id = match_checks.group(1)
        limit = int((event.get("queryStringParameters") or {}).get("limit", 50))
        checks = storage.get_checks(mon_id, limit=limit)
        return build_response(200, [c.to_dict() for c in checks])

    match_pause = re.match(r"^/api/monitors/([^/]+)/pause$", path)
    if match_pause and http_method.upper() == "POST":
        mon_id = match_pause.group(1)
        mon = storage.get_monitor(mon_id)
        if not mon:
            return build_response(404, {"error": "Monitor not found"})
        mon.status = "PAUSED"
        storage.save_monitor(mon)
        return build_response(200, mon.to_dict())

    match_resume = re.match(r"^/api/monitors/([^/]+)/resume$", path)
    if match_resume and http_method.upper() == "POST":
        mon_id = match_resume.group(1)
        mon = storage.get_monitor(mon_id)
        if not mon:
            return build_response(404, {"error": "Monitor not found"})
        mon.status = "PENDING"
        storage.save_monitor(mon)
        return build_response(200, mon.to_dict())

    match_single = re.match(r"^/api/monitors/([^/]+)$", path)
    if match_single:
        mon_id = match_single.group(1)
        if http_method.upper() == "GET":
            mon = storage.get_monitor(mon_id)
            if not mon:
                return build_response(404, {"error": "Monitor not found"})
            return build_response(200, mon.to_dict())

        if http_method.upper() == "PUT":
            mon = storage.get_monitor(mon_id)
            if not mon:
                return build_response(404, {"error": "Monitor not found"})
            body = parse_body(event)

            # If URL changed, validate SSRF
            new_url = body.get("url")
            if new_url and new_url != mon.url:
                is_valid, err_msg, _ = validate_target_url(new_url)
                if not is_valid:
                    return build_response(400, {"error": f"Invalid target URL: {err_msg}"})
                mon.url = new_url

            if "name" in body: mon.name = body["name"]
            if "method" in body: mon.method = body["method"].upper()
            if "interval_seconds" in body: mon.interval_seconds = int(body["interval_seconds"])
            if "timeout_seconds" in body: mon.timeout_seconds = int(body["timeout_seconds"])
            if "expected_status" in body: mon.expected_status = int(body["expected_status"])
            if "headers" in body: mon.headers = body["headers"]
            if "body" in body: mon.body = body["body"]
            if "tags" in body: mon.tags = body["tags"]
            if "alert_email" in body: mon.alert_email = body["alert_email"]
            if "failure_threshold" in body: mon.failure_threshold = int(body["failure_threshold"])
            if "recovery_threshold" in body: mon.recovery_threshold = int(body["recovery_threshold"])

            storage.save_monitor(mon)
            return build_response(200, mon.to_dict())

        if http_method.upper() == "DELETE":
            deleted = storage.delete_monitor(mon_id)
            if not deleted:
                return build_response(404, {"error": "Monitor not found"})
            return build_response(200, {"message": "Monitor deleted successfully", "id": mon_id})

    return build_response(404, {"error": f"Route not found: {http_method} {path}"})
