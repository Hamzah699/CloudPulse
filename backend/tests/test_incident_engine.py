"""
Unit tests for Incident Management Engine and state machine transitions.
"""

import pytest
from backend.core.models import Monitor, CheckResult, Incident
from backend.core.incident_engine import process_check_result, IncidentEventType


def test_consecutive_failures_and_incident_opening():
    monitor = Monitor(
        name="Test API",
        url="https://api.example.com",
        failure_threshold=2,
        recovery_threshold=2
    )

    # 1st failure -> monitor DEGRADED, no incident yet
    check1 = CheckResult(
        monitor_id=monitor.id,
        status="DOWN",
        status_code=500,
        error_message="Internal Server Error"
    )
    mon, inc, event = process_check_result(monitor, check1, active_incident=None)
    assert mon.status == "DEGRADED"
    assert mon.consecutive_failures == 1
    assert event == IncidentEventType.DEGRADED
    assert inc is None

    # 2nd failure -> threshold reached (2), incident opened!
    check2 = CheckResult(
        monitor_id=monitor.id,
        status="DOWN",
        status_code=500,
        error_message="Internal Server Error"
    )
    mon, inc, event = process_check_result(mon, check2, active_incident=None)
    assert mon.status == "DOWN"
    assert mon.consecutive_failures == 2
    assert event == IncidentEventType.INCIDENT_OPENED
    assert inc is not None
    assert inc.status == "OPEN"
    assert inc.consecutive_failures == 2


def test_ongoing_incident_updates():
    monitor = Monitor(
        name="Test API",
        url="https://api.example.com",
        failure_threshold=2,
        consecutive_failures=2
    )
    active_inc = Incident(
        monitor_id=monitor.id,
        monitor_name=monitor.name,
        monitor_url=monitor.url,
        status="OPEN",
        consecutive_failures=2
    )

    # 3rd failure -> incident ongoing, count incremented
    check3 = CheckResult(
        monitor_id=monitor.id,
        status="DOWN",
        status_code=503,
        error_message="Service Unavailable"
    )
    mon, inc, event = process_check_result(monitor, check3, active_incident=active_inc)
    assert mon.status == "DOWN"
    assert mon.consecutive_failures == 3
    assert inc.consecutive_failures == 3
    assert event == IncidentEventType.INCIDENT_ONGOING


def test_recovery_threshold_and_incident_resolution():
    monitor = Monitor(
        name="Test API",
        url="https://api.example.com",
        failure_threshold=2,
        recovery_threshold=2,
        status="DOWN",
        consecutive_failures=3
    )
    active_inc = Incident(
        monitor_id=monitor.id,
        monitor_name=monitor.name,
        monitor_url=monitor.url,
        status="OPEN",
        started_at="2026-10-12T10:00:00Z"
    )

    # 1st success -> recovering, but threshold is 2 so still degraded/recovering
    check_pass1 = CheckResult(
        monitor_id=monitor.id,
        status="UP",
        status_code=200,
        timestamp="2026-10-12T10:01:00Z"
    )
    mon, inc, event = process_check_result(monitor, check_pass1, active_incident=active_inc)
    assert mon.status == "DEGRADED"
    assert mon.consecutive_successes == 1
    assert event == IncidentEventType.RECOVERING
    assert inc.status == "OPEN"

    # 2nd success -> recovery threshold reached (2), incident resolved!
    check_pass2 = CheckResult(
        monitor_id=monitor.id,
        status="UP",
        status_code=200,
        timestamp="2026-10-12T10:02:00Z"
    )
    mon, inc, event = process_check_result(mon, check_pass2, active_incident=inc)
    assert mon.status == "UP"
    assert mon.consecutive_successes == 2
    assert event == IncidentEventType.INCIDENT_RESOLVED
    assert inc.status == "RESOLVED"
    assert inc.resolved_at is not None
    assert inc.duration_seconds is not None
    assert inc.duration_seconds > 0
