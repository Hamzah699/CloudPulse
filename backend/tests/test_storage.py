"""
Unit tests for LocalStorage implementation (SQLite).
"""

import os
import tempfile
import pytest
from backend.storage.local_storage import LocalStorage
from backend.core.models import Monitor, CheckResult, Incident


@pytest.fixture
def temp_storage():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    storage = LocalStorage(db_path=path)
    yield storage
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError:
        pass


def test_monitor_crud(temp_storage):
    mon = Monitor(
        name="Test Mon",
        url="https://api.example.com/health",
        method="GET",
        interval_seconds=60,
        expected_status=200,
        tags=["prod", "api"]
    )
    temp_storage.save_monitor(mon)

    retrieved = temp_storage.get_monitor(mon.id)
    assert retrieved is not None
    assert retrieved.name == "Test Mon"
    assert retrieved.url == "https://api.example.com/health"
    assert "prod" in retrieved.tags

    # Update
    retrieved.name = "Updated Mon"
    retrieved.status = "UP"
    temp_storage.save_monitor(retrieved)

    updated = temp_storage.get_monitor(mon.id)
    assert updated.name == "Updated Mon"
    assert updated.status == "UP"

    # List
    all_monitors = temp_storage.list_monitors()
    assert len(all_monitors) == 1

    # Delete
    deleted = temp_storage.delete_monitor(mon.id)
    assert deleted
    assert temp_storage.get_monitor(mon.id) is None


def test_check_history(temp_storage):
    mon_id = "test-mon-123"
    check1 = CheckResult(monitor_id=mon_id, status="UP", status_code=200, latency_ms=45.5, timestamp="2026-10-12T10:00:00Z")
    check2 = CheckResult(monitor_id=mon_id, status="DOWN", status_code=500, latency_ms=60.0, timestamp="2026-10-12T10:01:00Z")

    temp_storage.save_check(check1)
    temp_storage.save_check(check2)

    checks = temp_storage.get_checks(mon_id)
    assert len(checks) == 2
    assert checks[0].timestamp == "2026-10-12T10:01:00Z"
    assert checks[0].status == "DOWN"


def test_incident_lifecycle(temp_storage):
    mon_id = "test-mon-456"
    inc = Incident(
        monitor_id=mon_id,
        monitor_name="Billing API",
        monitor_url="https://billing.example.com",
        status="OPEN",
        cause="500 Internal Error"
    )
    temp_storage.save_incident(inc)

    active = temp_storage.get_active_incident(mon_id)
    assert active is not None
    assert active.id == inc.id
    assert active.status == "OPEN"

    # Resolve incident
    inc.status = "RESOLVED"
    inc.resolved_at = "2026-10-12T10:05:00Z"
    temp_storage.save_incident(inc)

    # Active should now be None
    active_after = temp_storage.get_active_incident(mon_id)
    assert active_after is None
