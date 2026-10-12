"""
Sample Dataset Seeder for CloudPulse Presentation & Evaluation.
Populates rich, realistic enterprise monitors, 24-hour socket check telemetry,
active/acknowledged/resolved incidents, and Amazon SNS alert dispatch history.
"""

import os
import sys
import time
import random
import uuid

# Ensure root directory is in sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.storage.local_storage import LocalStorage
from backend.core.models import Monitor, CheckResult, Incident
from backend.notify.notifier import LocalNotifier


def seed_presentation_dataset():
    db_path = os.path.join(BASE_DIR, "cloudpulse.db")
    storage = LocalStorage(db_path=db_path)
    print(f"[CloudPulse Seeder] Connecting to database: {db_path}")

    # Clear existing demo data for clean presentation setup
    existing = storage.list_monitors()
    for m in existing:
        storage.delete_monitor(m.id)
    LocalNotifier.clear()

    now_epoch = int(time.time())
    one_hour = 3600
    one_day = 86400

    # --------------------------------------------------------------------------
    # 1. Define Realistic Enterprise Monitors
    # --------------------------------------------------------------------------
    monitors_data = [
        {
            "id": "mon_auth_prod",
            "name": "Auth & SSO Service (Cognito Gateway)",
            "url": "https://dns.google",
            "method": "GET",
            "interval_seconds": 60,
            "timeout_seconds": 5,
            "expected_status": 200,
            "tags": ["production", "auth", "critical", "tier-0"],
            "alert_email": "secops-alerts@cloudpulse.io",
            "status": "UP",
            "uptime_percentage": 99.95,
            "total_checks": 1440,
            "successful_checks": 1439,
            "last_latency_ms": 28.4,
            "last_status_code": 200,
            "failure_threshold": 2,
            "recovery_threshold": 2,
            "base_latency": 25.0,
            "ip": "8.8.8.8"
        },
        {
            "id": "mon_billing_api",
            "name": "Stripe Billing & Subscriptions API",
            "url": "https://httpbin.org/status/200",
            "method": "POST",
            "interval_seconds": 60,
            "timeout_seconds": 10,
            "expected_status": 200,
            "tags": ["billing", "payments", "production", "pci-dss"],
            "alert_email": "finance-devops@cloudpulse.io",
            "status": "UP",
            "uptime_percentage": 99.82,
            "total_checks": 1440,
            "successful_checks": 1437,
            "last_latency_ms": 78.5,
            "last_status_code": 200,
            "failure_threshold": 2,
            "recovery_threshold": 2,
            "base_latency": 75.0,
            "ip": "54.237.226.164"
        },
        {
            "id": "mon_portal_cdn",
            "name": "Customer Web Portal (CloudFront Edge)",
            "url": "https://one.one.one.one",
            "method": "GET",
            "interval_seconds": 60,
            "timeout_seconds": 5,
            "expected_status": 200,
            "tags": ["frontend", "cdn", "cloudfront", "edge"],
            "alert_email": "web-team@cloudpulse.io",
            "status": "UP",
            "uptime_percentage": 100.0,
            "total_checks": 1440,
            "successful_checks": 1440,
            "last_latency_ms": 14.2,
            "last_status_code": 200,
            "failure_threshold": 2,
            "recovery_threshold": 2,
            "base_latency": 15.0,
            "ip": "1.1.1.1"
        },
        {
            "id": "mon_catalog_api",
            "name": "Product Catalog & Search Microservice",
            "url": "https://www.githubstatus.com",
            "method": "GET",
            "interval_seconds": 60,
            "timeout_seconds": 10,
            "expected_status": 200,
            "tags": ["api", "catalog", "microservice"],
            "alert_email": "catalog-oncall@cloudpulse.io",
            "status": "UP",
            "uptime_percentage": 99.45,
            "total_checks": 1440,
            "successful_checks": 1432,
            "last_latency_ms": 112.0,
            "last_status_code": 200,
            "failure_threshold": 2,
            "recovery_threshold": 2,
            "base_latency": 110.0,
            "ip": "140.82.121.4"
        },
        {
            "id": "mon_logistics_outage",
            "name": "Third-Party Logistics Webhook Gateway",
            "url": "https://httpbin.org/status/503",
            "method": "POST",
            "interval_seconds": 60,
            "timeout_seconds": 5,
            "expected_status": 200,
            "tags": ["external", "partners", "logistics", "webhooks"],
            "alert_email": "partner-integrations@cloudpulse.io",
            "status": "DOWN",
            "uptime_percentage": 94.20,
            "total_checks": 1440,
            "successful_checks": 1356,
            "last_latency_ms": 240.5,
            "last_status_code": 503,
            "consecutive_failures": 4,
            "failure_threshold": 2,
            "recovery_threshold": 2,
            "base_latency": 220.0,
            "ip": "52.86.104.19"
        },
        {
            "id": "mon_legacy_paused",
            "name": "Legacy Reports Exporter (Batch Service)",
            "url": "https://httpbin.org/status/200",
            "method": "GET",
            "interval_seconds": 300,
            "timeout_seconds": 15,
            "expected_status": 200,
            "tags": ["legacy", "batch", "paused"],
            "alert_email": "ops-archive@cloudpulse.io",
            "status": "PAUSED",
            "uptime_percentage": 98.70,
            "total_checks": 288,
            "successful_checks": 284,
            "last_latency_ms": 185.0,
            "last_status_code": 200,
            "failure_threshold": 3,
            "recovery_threshold": 2,
            "base_latency": 180.0,
            "ip": "34.195.122.50"
        }
    ]

    print(f"[CloudPulse Seeder] Creating {len(monitors_data)} enterprise monitors...")
    for m_info in monitors_data:
        base_lat = m_info.pop("base_latency")
        target_ip = m_info.pop("ip")

        monitor = Monitor(
            id=m_info["id"],
            name=m_info["name"],
            url=m_info["url"],
            method=m_info["method"],
            interval_seconds=m_info["interval_seconds"],
            timeout_seconds=m_info["timeout_seconds"],
            expected_status=m_info["expected_status"],
            tags=m_info["tags"],
            alert_email=m_info["alert_email"],
            status=m_info["status"],
            uptime_percentage=m_info["uptime_percentage"],
            total_checks=m_info["total_checks"],
            successful_checks=m_info["successful_checks"],
            last_latency_ms=m_info["last_latency_ms"],
            last_status_code=m_info["last_status_code"],
            consecutive_failures=m_info.get("consecutive_failures", 0),
            failure_threshold=m_info["failure_threshold"],
            recovery_threshold=m_info["recovery_threshold"],
            last_checked_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch - 30)),
            user_id="default_user"
        )
        storage.save_monitor(monitor)

        # ----------------------------------------------------------------------
        # 2. Generate 30 Historical Telemetry Checks per Monitor (For Recharts)
        # ----------------------------------------------------------------------
        print(f"  -> Generating 30 socket telemetry checks for '{monitor.name}'...")
        for i in range(30):
            # Check timestamps spaced every 2 minutes backwards
            check_epoch = now_epoch - ((29 - i) * 120)
            check_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(check_epoch))

            # Realistic random variations
            dns_ms = round(random.uniform(2.5, 6.5), 1)
            connect_ms = round(random.uniform(8.0, 18.0), 1)
            ttfb_ms = round(random.uniform(15.0, 35.0), 1)

            if monitor.id == "mon_logistics_outage" and i >= 26:
                # The last 4 checks failed (outage!)
                check_status = "DOWN"
                code = 503
                err_msg = "HTTP 503 Service Unavailable: Partner Gateway Timeout"
                tot_ms = round(base_lat + random.uniform(20.0, 80.0), 1)
            else:
                check_status = "UP"
                code = 200
                err_msg = None
                jitter = random.uniform(-8.0, 12.0)
                tot_ms = max(5.0, round(base_lat + jitter, 1))

            check = CheckResult(
                id=f"chk_{monitor.id}_{i}",
                monitor_id=monitor.id,
                timestamp=check_iso,
                epoch_timestamp=check_epoch,
                status=check_status,
                status_code=code,
                latency_ms=tot_ms,
                dns_time_ms=dns_ms,
                connect_time_ms=connect_ms,
                ttfb_ms=ttfb_ms,
                error_message=err_msg,
                target_ip=target_ip,
                checked_from_region="us-east-1",
                headers={
                    "server": "nginx/1.24",
                    "content-type": "application/json",
                    "x-amz-cf-id": f"cf_{uuid.uuid4().hex[:8]}"
                }
            )
            storage.save_check(check)

    # --------------------------------------------------------------------------
    # 3. Create Realistic Incidents (OPEN, ACKNOWLEDGED, RESOLVED)
    # --------------------------------------------------------------------------
    print("[CloudPulse Seeder] Creating incident records (Active & Historical)...")

    # Incident 1: Active OPEN Incident on Logistics Webhook
    inc_open = Incident(
        id="inc_active_outage_01",
        monitor_id="mon_logistics_outage",
        monitor_name="Third-Party Logistics Webhook Gateway",
        monitor_url="https://httpbin.org/status/503",
        status="OPEN",
        started_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch - 1800)), # 30 mins ago
        cause="HTTP 503 Service Unavailable: Partner Gateway Timeout",
        last_status_code=503,
        consecutive_failures=4,
        alert_sent=True,
        alert_recipient="partner-integrations@cloudpulse.io",
        user_id="default_user"
    )
    storage.save_incident(inc_open)

    # Incident 2: ACKNOWLEDGED Incident on Product Catalog
    inc_ack = Incident(
        id="inc_catalog_failover_02",
        monitor_id="mon_catalog_api",
        monitor_name="Product Catalog & Search Microservice",
        monitor_url="https://www.githubstatus.com",
        status="ACKNOWLEDGED",
        started_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch - 7200)), # 2 hrs ago
        cause="Connection timeout after 10s: Database read replica failover",
        last_status_code=504,
        consecutive_failures=3,
        alert_sent=True,
        alert_recipient="catalog-oncall@cloudpulse.io",
        acknowledged_by="lead-sre@cloudpulse.io",
        acknowledged_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch - 6800)),
        user_id="default_user"
    )
    storage.save_incident(inc_ack)

    # Incident 3: RESOLVED Incident on Stripe Billing Gateway
    inc_res1 = Incident(
        id="inc_billing_resolved_03",
        monitor_id="mon_billing_api",
        monitor_name="Stripe Billing & Subscriptions API",
        monitor_url="https://httpbin.org/status/200",
        status="RESOLVED",
        started_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch - 86400)), # 24 hrs ago
        resolved_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch - 85560)), # 14 mins duration
        duration_seconds=840,
        cause="HTTP 502 Bad Gateway: Upstream connection pool exhausted",
        last_status_code=200,
        consecutive_failures=2,
        alert_sent=True,
        alert_recipient="finance-devops@cloudpulse.io",
        user_id="default_user"
    )
    storage.save_incident(inc_res1)

    # Incident 4: RESOLVED Incident on Customer Portal CDN
    inc_res2 = Incident(
        id="inc_portal_resolved_04",
        monitor_id="mon_portal_cdn",
        monitor_name="Customer Web Portal (CloudFront Edge)",
        monitor_url="https://one.one.one.one",
        status="RESOLVED",
        started_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch - 172800)), # 48 hrs ago
        resolved_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch - 172440)), # 6 mins duration
        duration_seconds=360,
        cause="DNS resolution failure at regional edge point of presence",
        last_status_code=200,
        consecutive_failures=2,
        alert_sent=True,
        alert_recipient="web-team@cloudpulse.io",
        user_id="default_user"
    )
    storage.save_incident(inc_res2)

    # --------------------------------------------------------------------------
    # 4. Populate Amazon SNS Alert Notification Inbox
    # --------------------------------------------------------------------------
    print("[CloudPulse Seeder] Populating Amazon SNS alert history inbox...")
    alerts = [
        {
            "id": "notif_01",
            "subject": "[CloudPulse Alert] INCIDENT OPEN: Third-Party Logistics Webhook Gateway",
            "monitor_id": "mon_logistics_outage",
            "monitor_name": "Third-Party Logistics Webhook Gateway",
            "monitor_url": "https://httpbin.org/status/503",
            "status": "OPEN",
            "event_type": "INCIDENT_OPENED",
            "cause": "HTTP 503 Service Unavailable: Partner Gateway Timeout (Consecutive failures: 4)",
            "recipient": "partner-integrations@cloudpulse.io",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch - 1800)),
            "duration_seconds": None
        },
        {
            "id": "notif_02",
            "subject": "[CloudPulse Alert] INCIDENT OPEN: Product Catalog & Search Microservice",
            "monitor_id": "mon_catalog_api",
            "monitor_name": "Product Catalog & Search Microservice",
            "monitor_url": "https://www.githubstatus.com",
            "status": "ACKNOWLEDGED",
            "event_type": "INCIDENT_OPENED",
            "cause": "Connection timeout after 10s: Database read replica failover",
            "recipient": "catalog-oncall@cloudpulse.io",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch - 7200)),
            "duration_seconds": None
        },
        {
            "id": "notif_03",
            "subject": "[CloudPulse Alert] RESOLVED: Stripe Billing & Subscriptions API",
            "monitor_id": "mon_billing_api",
            "monitor_name": "Stripe Billing & Subscriptions API",
            "monitor_url": "https://httpbin.org/status/200",
            "status": "RESOLVED",
            "event_type": "INCIDENT_RESOLVED",
            "cause": "HTTP 502 Bad Gateway: Upstream connection pool exhausted",
            "recipient": "finance-devops@cloudpulse.io",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch - 85560)),
            "duration_seconds": 840
        },
        {
            "id": "notif_04",
            "subject": "[CloudPulse Alert] RESOLVED: Customer Web Portal (CloudFront Edge)",
            "monitor_id": "mon_portal_cdn",
            "monitor_name": "Customer Web Portal (CloudFront Edge)",
            "monitor_url": "https://one.one.one.one",
            "status": "RESOLVED",
            "event_type": "INCIDENT_RESOLVED",
            "cause": "DNS resolution failure at regional edge point of presence",
            "recipient": "web-team@cloudpulse.io",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_epoch - 172440)),
            "duration_seconds": 360
        }
    ]

    for a in alerts:
        storage.save_notification(a)
        LocalNotifier.notifications.append(a)

    stats = storage.get_summary_stats()
    print("\n" + "=" * 60)
    print("  CLOUDPULSE SAMPLE PRESENTATION DATASET SEEDED SUCCESSFULLY")
    print("=" * 60)
    print(f"  Total Monitors:    {stats['total_monitors']}")
    print(f"  Operational (UP):  {stats['up_count']}")
    print(f"  Outage (DOWN):     {stats['down_count']}")
    print(f"  Paused:            {stats['paused_count']}")
    print(f"  Overall Uptime:    {stats['overall_uptime_percentage']}%")
    print(f"  Average Latency:   {stats['average_latency_ms']} ms")
    print(f"  Open Incidents:    {stats['open_incidents_count']}")
    print(f"  SNS Alerts Stored: {len(LocalNotifier.notifications)}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    seed_presentation_dataset()
