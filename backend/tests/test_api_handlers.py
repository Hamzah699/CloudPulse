"""
Integration tests for Lambda API Handlers.
Simulates API Gateway requests against the router and verifies responses.
"""

import os
import json
import tempfile
import pytest

from backend.handlers.api import handler
from backend.storage import get_storage
from backend.core.auth import generate_local_token


@pytest.fixture(autouse=True)
def setup_test_env():
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.environ["USE_LOCAL_STORAGE"] = "true"
    os.environ["SQLITE_DB_PATH"] = db_path
    get_storage(reset=True)
    yield
    try:
        if os.path.exists(db_path):
            os.remove(db_path)
    except OSError:
        pass


def make_request(method: str, path: str, body: dict = None, token: str = None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    event = {
        "httpMethod": method,
        "path": path,
        "headers": headers,
        "body": json.dumps(body) if body else None,
        "requestContext": {}
    }
    return handler(event, None)


def test_public_health_check():
    res = make_request("GET", "/health")
    assert res["statusCode"] == 200
    data = json.loads(res["body"])
    assert data["status"] == "healthy"


def test_auth_login_and_token_generation():
    res = make_request("POST", "/api/auth/login", {"email": "test@cloudpulse.io"})
    assert res["statusCode"] == 200
    data = json.loads(res["body"])
    assert "token" in data
    assert data["user"]["email"] == "test@cloudpulse.io"


def test_unauthorized_access():
    res = make_request("GET", "/api/monitors")
    assert res["statusCode"] == 401


def test_monitor_crud_and_ssrf_protection():
    token = generate_local_token("test_user_1", "test@cloudpulse.io")

    # 1. Attempt to add monitor with SSRF forbidden URL (localhost)
    res_bad = make_request(
        "POST",
        "/api/monitors",
        {"name": "Localhost Attack", "url": "http://127.0.0.1:8080/secret"},
        token=token
    )
    assert res_bad["statusCode"] == 400
    assert "Invalid target URL" in json.loads(res_bad["body"])["error"]

    # 2. Add valid public monitor
    res_good = make_request(
        "POST",
        "/api/monitors",
        {
            "name": "Google DNS",
            "url": "https://dns.google",
            "interval_seconds": 60,
            "expected_status": 200,
            "tags": ["dns", "public"]
        },
        token=token
    )
    assert res_good["statusCode"] == 201
    mon_data = json.loads(res_good["body"])
    mon_id = mon_data["id"]
    assert mon_data["name"] == "Google DNS"

    # 3. List monitors
    res_list = make_request("GET", "/api/monitors", token=token)
    assert res_list["statusCode"] == 200
    monitors = json.loads(res_list["body"])
    assert len(monitors) == 1

    # 4. Get stats
    res_stats = make_request("GET", "/api/stats", token=token)
    assert res_stats["statusCode"] == 200
    stats = json.loads(res_stats["body"])
    assert stats["total_monitors"] == 1

    # 5. Pause monitor
    res_pause = make_request("POST", f"/api/monitors/{mon_id}/pause", token=token)
    assert res_pause["statusCode"] == 200
    assert json.loads(res_pause["body"])["status"] == "PAUSED"

    # 6. Resume monitor
    res_resume = make_request("POST", f"/api/monitors/{mon_id}/resume", token=token)
    assert res_resume["statusCode"] == 200
    assert json.loads(res_resume["body"])["status"] == "PENDING"

    # 7. Delete monitor
    res_del = make_request("DELETE", f"/api/monitors/{mon_id}", token=token)
    assert res_del["statusCode"] == 200

    # 8. Verify deleted
    res_check = make_request("GET", f"/api/monitors/{mon_id}", token=token)
    assert res_check["statusCode"] == 404
