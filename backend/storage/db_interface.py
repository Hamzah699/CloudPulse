"""
Abstract Database Interface for CloudPulse.
Defines the uniform contract implemented by both DynamoDBStorage and LocalStorage.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
try:
    from ..core.models import Monitor, CheckResult, Incident
except (ImportError, ValueError):
    from core.models import Monitor, CheckResult, Incident


class DatabaseInterface(ABC):
    @abstractmethod
    def save_monitor(self, monitor: Monitor) -> None:
        pass

    @abstractmethod
    def get_monitor(self, monitor_id: str) -> Optional[Monitor]:
        pass

    @abstractmethod
    def list_monitors(self, user_id: Optional[str] = None) -> List[Monitor]:
        pass

    @abstractmethod
    def delete_monitor(self, monitor_id: str) -> bool:
        pass

    @abstractmethod
    def save_check(self, check: CheckResult) -> None:
        pass

    @abstractmethod
    def get_checks(self, monitor_id: str, limit: int = 50) -> List[CheckResult]:
        pass

    @abstractmethod
    def save_incident(self, incident: Incident) -> None:
        pass

    @abstractmethod
    def get_incident(self, incident_id: str) -> Optional[Incident]:
        pass

    @abstractmethod
    def list_incidents(self, monitor_id: Optional[str] = None, status: Optional[str] = None) -> List[Incident]:
        pass

    @abstractmethod
    def get_active_incident(self, monitor_id: str) -> Optional[Incident]:
        pass

    @abstractmethod
    def get_summary_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        pass
