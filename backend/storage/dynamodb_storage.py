"""
AWS DynamoDB Storage implementation for CloudPulse production environment.
Utilizes Amazon DynamoDB with Boto3 SDK, handles Decimal conversions, and enforces no silent mock fallbacks.
"""

import os
import boto3
from boto3.dynamodb.conditions import Key, Attr
from decimal import Decimal
from typing import List, Optional, Dict, Any

from .db_interface import DatabaseInterface
from ..core.models import Monitor, CheckResult, Incident


def decimal_to_native(obj: Any) -> Any:
    """Recursively converts DynamoDB Decimal objects to int or float."""
    if isinstance(obj, list):
        return [decimal_to_native(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: decimal_to_native(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    return obj


def native_to_decimal(obj: Any) -> Any:
    """Recursively converts float values to Decimal for DynamoDB storage."""
    if isinstance(obj, list):
        return [native_to_decimal(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: native_to_decimal(v) for k, v in obj.items()}
    elif isinstance(obj, float):
        return Decimal(str(obj))
    return obj


class DynamoDBStorage(DatabaseInterface):
    def __init__(self):
        region = os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-east-1"))
        self.dynamodb = boto3.resource("dynamodb", region_name=region)
        
        self.monitors_table_name = os.environ.get("MONITORS_TABLE", "CloudPulseMonitors")
        self.checks_table_name = os.environ.get("CHECKS_TABLE", "CloudPulseChecks")
        self.incidents_table_name = os.environ.get("INCIDENTS_TABLE", "CloudPulseIncidents")

        self.monitors_table = self.dynamodb.Table(self.monitors_table_name)
        self.checks_table = self.dynamodb.Table(self.checks_table_name)
        self.incidents_table = self.dynamodb.Table(self.incidents_table_name)

    def save_monitor(self, monitor: Monitor) -> None:
        data = native_to_decimal(monitor.to_dict())
        self.monitors_table.put_item(Item=data)

    def get_monitor(self, monitor_id: str) -> Optional[Monitor]:
        response = self.monitors_table.get_item(Key={"id": monitor_id})
        item = response.get("Item")
        if not item:
            return None
        return Monitor.from_dict(decimal_to_native(item))

    def list_monitors(self, user_id: Optional[str] = None) -> List[Monitor]:
        if user_id:
            # If user_id is provided, query using user_id index or scan with filter
            response = self.monitors_table.scan(
                FilterExpression=Attr("user_id").eq(user_id)
            )
        else:
            response = self.monitors_table.scan()

        items = response.get("Items", [])
        return [Monitor.from_dict(decimal_to_native(item)) for item in items]

    def delete_monitor(self, monitor_id: str) -> bool:
        self.monitors_table.delete_item(Key={"id": monitor_id})
        return True

    def save_check(self, check: CheckResult) -> None:
        data = native_to_decimal(check.to_dict())
        # Add TTL for automatic DynamoDB retention cleanup (30 days)
        data["ttl"] = check.epoch_timestamp + (30 * 86400)
        self.checks_table.put_item(Item=data)

    def get_checks(self, monitor_id: str, limit: int = 50) -> List[CheckResult]:
        response = self.checks_table.query(
            KeyConditionExpression=Key("monitor_id").eq(monitor_id),
            ScanIndexForward=False,  # Descending order (newest first)
            Limit=limit
        )
        items = response.get("Items", [])
        return [CheckResult.from_dict(decimal_to_native(item)) for item in items]

    def save_incident(self, incident: Incident) -> None:
        data = native_to_decimal(incident.to_dict())
        self.incidents_table.put_item(Item=data)

    def get_incident(self, incident_id: str) -> Optional[Incident]:
        response = self.incidents_table.get_item(Key={"id": incident_id})
        item = response.get("Item")
        if not item:
            return None
        return Incident.from_dict(decimal_to_native(item))

    def list_incidents(self, monitor_id: Optional[str] = None, status: Optional[str] = None) -> List[Incident]:
        scan_kwargs = {}
        filter_expr = None

        if monitor_id and status:
            filter_expr = Attr("monitor_id").eq(monitor_id) & Attr("status").eq(status)
        elif monitor_id:
            filter_expr = Attr("monitor_id").eq(monitor_id)
        elif status:
            filter_expr = Attr("status").eq(status)

        if filter_expr:
            scan_kwargs["FilterExpression"] = filter_expr

        response = self.incidents_table.scan(**scan_kwargs)
        items = response.get("Items", [])
        
        incidents = [Incident.from_dict(decimal_to_native(item)) for item in items]
        incidents.sort(key=lambda x: x.started_at, reverse=True)
        return incidents

    def get_active_incident(self, monitor_id: str) -> Optional[Incident]:
        response = self.incidents_table.scan(
            FilterExpression=Attr("monitor_id").eq(monitor_id) & Attr("status").is_in(["OPEN", "ACKNOWLEDGED"])
        )
        items = response.get("Items", [])
        if not items:
            return None
        items.sort(key=lambda x: x.get("started_at", ""), reverse=True)
        return Incident.from_dict(decimal_to_native(items[0]))

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
