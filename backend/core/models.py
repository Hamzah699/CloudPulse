"""
Domain Models for CloudPulse.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List
import time
import uuid


@dataclass
class Monitor:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    url: str = ""
    method: str = "GET"
    interval_seconds: int = 60
    timeout_seconds: int = 10
    expected_status: int = 200
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    alert_email: Optional[str] = None
    failure_threshold: int = 2      # Consecutive failures before opening incident
    recovery_threshold: int = 2     # Consecutive successes before resolving incident
    status: str = "PENDING"         # UP, DOWN, PAUSED, DEGRADED, PENDING
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    last_checked_at: Optional[str] = None
    last_status_code: Optional[int] = None
    last_latency_ms: Optional[float] = None
    uptime_percentage: float = 100.0
    total_checks: int = 0
    successful_checks: int = 0
    created_at: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    updated_at: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    user_id: str = "default_user"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Monitor":
        fields = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**fields)


@dataclass
class CheckResult:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    monitor_id: str = ""
    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    epoch_timestamp: int = field(default_factory=lambda: int(time.time()))
    status: str = "UP"              # UP, DOWN
    status_code: Optional[int] = None
    latency_ms: float = 0.0
    dns_time_ms: float = 0.0
    connect_time_ms: float = 0.0
    ttfb_ms: float = 0.0
    error_message: Optional[str] = None
    target_ip: Optional[str] = None
    checked_from_region: str = "us-east-1"
    headers: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CheckResult":
        fields = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**fields)


@dataclass
class Incident:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    monitor_id: str = ""
    monitor_name: str = ""
    monitor_url: str = ""
    status: str = "OPEN"            # OPEN, ACKNOWLEDGED, RESOLVED
    started_at: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    resolved_at: Optional[str] = None
    duration_seconds: Optional[int] = None
    cause: str = "Connection timeout or error"
    last_status_code: Optional[int] = None
    consecutive_failures: int = 1
    alert_sent: bool = False
    alert_recipient: Optional[str] = None
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[str] = None
    user_id: str = "default_user"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Incident":
        fields = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**fields)
