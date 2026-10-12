"""
Local Development Server for CloudPulse.
Emulates AWS API Gateway and EventBridge Scheduler locally without requiring AWS credentials.
Executes the exact same Lambda handler code as deployed to AWS.
"""

import os
import sys
import json
import time
import threading
from typing import Dict, Any

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Force local environment defaults
os.environ.setdefault("USE_LOCAL_STORAGE", "true")
os.environ.setdefault("STORAGE_BACKEND", "sqlite")
os.environ.setdefault("NOTIFICATION_BACKEND", "local")
os.environ.setdefault("SQLITE_DB_PATH", os.path.join(BASE_DIR, "cloudpulse.db"))
os.environ.setdefault("ALLOW_ANONYMOUS_DEV", "true")

from flask import Flask, request, Response
from backend.handlers.api import handler as api_handler
from backend.handlers.checker import handler as checker_handler
from backend.storage import get_storage
from backend.core.models import Monitor

app = Flask(__name__)


def flask_to_lambda_event(flask_req) -> Dict[str, Any]:
    """Converts a Flask request into an AWS API Gateway event dictionary."""
    headers = {k: v for k, v in flask_req.headers.items()}
    query_params = {k: v for k, v in flask_req.args.items()}
    body_data = flask_req.get_data(as_text=True)

    return {
        "httpMethod": flask_req.method,
        "path": flask_req.path,
        "rawPath": flask_req.path,
        "headers": headers,
        "queryStringParameters": query_params if query_params else None,
        "body": body_data if body_data else None,
        "isBase64Encoded": False,
        "requestContext": {
            "http": {
                "method": flask_req.method,
                "path": flask_req.path,
                "sourceIp": flask_req.remote_addr
            },
            "timeEpoch": int(time.time() * 1000)
        }
    }


@app.route("/", defaults={"path": ""}, methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
@app.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
def gateway_proxy(path):
    """Proxies all requests directly into the API Gateway Lambda handler."""
    event = flask_to_lambda_event(request)
    result = api_handler(event, None)

    status_code = result.get("statusCode", 200)
    res_headers = result.get("headers", {})
    body = result.get("body", "")

    response = Response(
        response=body,
        status=status_code,
        headers=res_headers,
        mimetype="application/json"
    )
    return response


def run_scheduler_loop(interval_seconds: int = 60):
    """Background thread simulating Amazon EventBridge Scheduler rule."""
    print(f"[EventBridge Simulator] Scheduler active. Running health checks every {interval_seconds}s.")
    while True:
        try:
            time.sleep(interval_seconds)
            checker_handler({}, None)
        except Exception as e:
            print(f"[EventBridge Simulator Error] {e}")


def seed_demo_monitors_if_empty():
    """Seeds initial popular monitors if database is empty so dashboard displays immediate data."""
    storage = get_storage()
    existing = storage.list_monitors()
    if not existing:
        print("[CloudPulse Seed] Seeding demo monitors...")
        demo_monitors = [
            Monitor(
                name="Google DNS / Public Web",
                url="https://dns.google",
                interval_seconds=60,
                timeout_seconds=5,
                expected_status=200,
                tags=["production", "dns", "critical"],
                alert_email="alerts@cloudpulse.io"
            ),
            Monitor(
                name="Cloudflare 1.1.1.1 Portal",
                url="https://one.one.one.one",
                interval_seconds=60,
                timeout_seconds=5,
                expected_status=200,
                tags=["cdn", "production"],
                alert_email="devops@cloudpulse.io"
            ),
            Monitor(
                name="GitHub Status API",
                url="https://www.githubstatus.com",
                interval_seconds=60,
                timeout_seconds=5,
                expected_status=200,
                tags=["api", "external"],
                alert_email="team@cloudpulse.io"
            ),
            Monitor(
                name="HTTPBin Test Endpoint",
                url="https://httpbin.org/status/200",
                interval_seconds=60,
                timeout_seconds=10,
                expected_status=200,
                tags=["test", "api"],
                alert_email="admin@cloudpulse.io"
            )
        ]
        for m in demo_monitors:
            storage.save_monitor(m)
        print(f"[CloudPulse Seed] Added {len(demo_monitors)} monitors.")


if __name__ == "__main__":
    seed_demo_monitors_if_empty()

    # Start EventBridge simulation in background thread
    scheduler_thread = threading.Thread(target=run_scheduler_loop, args=(60,), daemon=True)
    scheduler_thread.start()

    print("\n" + "=" * 64)
    print("  CLOUDPULSE SERVERLESS UPTIME PLATFORM - LOCAL DEV SERVER")
    print("=" * 64)
    print("  Status:      Running on http://localhost:5000")
    print("  Database:    SQLite (DynamoDB Mirror)")
    print("  Scheduler:   EventBridge Background Simulation Active (60s)")
    print("  Auth:        Local JWT Provider / Cognito Simulation")
    print("  SSRF Guard:  ACTIVE (Validates all endpoints & redirects)")
    print("=" * 64 + "\n")

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
