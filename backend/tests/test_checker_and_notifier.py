"""
Tests for scheduled health checker Lambda handler and Notifier.
"""

import os
import tempfile
import pytest

from backend.handlers.checker import handler as checker_handler
from backend.storage import get_storage
from backend.core.models import Monitor
from backend.notify.notifier import get_notifier, LocalNotifier


@pytest.fixture(autouse=True)
def setup_checker_env():
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.environ["USE_LOCAL_STORAGE"] = "true"
    os.environ["SQLITE_DB_PATH"] = db_path
    os.environ["NOTIFICATION_BACKEND"] = "local"
    LocalNotifier.clear()
    storage = get_storage(reset=True)
    yield storage
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except OSError:
        pass


def test_scheduled_checker_execution(setup_checker_env):
    storage = setup_checker_env

    # Add a public monitor and a paused monitor
    m1 = Monitor(name="Google DNS", url="https://dns.google", status="PENDING")
    m2 = Monitor(name="Paused Mon", url="https://1.1.1.1", status="PAUSED")
    storage.save_monitor(m1)
    storage.save_monitor(m2)

    # Run scheduled checker handler
    summary = checker_handler({}, None)
    assert summary["monitors_checked"] == 1  # Only m1, m2 is paused!
    assert summary["up"] == 1 or summary["down"] == 1

    # Verify check was persisted
    checks = storage.get_checks(m1.id)
    assert len(checks) >= 1

    # Verify monitor status updated
    updated_m1 = storage.get_monitor(m1.id)
    assert updated_m1.status in ("UP", "DOWN", "DEGRADED")
    assert updated_m1.total_checks == 1


def test_notifier_records_alerts():
    notifier = get_notifier()
    m = Monitor(name="Test Service", url="https://api.test.com", alert_email="ops@cloudpulse.io")
    from backend.core.models import Incident
    inc = Incident(monitor_id=m.id, monitor_name=m.name, monitor_url=m.url, status="OPEN", cause="Timeout")

    sent = notifier.send_incident_alert(inc, m, "INCIDENT_OPENED")
    assert sent

    alerts = LocalNotifier.get_notifications()
    assert len(alerts) >= 1
    assert alerts[0]["monitor_name"] == "Test Service"
    assert alerts[0]["status"] == "OPEN"
