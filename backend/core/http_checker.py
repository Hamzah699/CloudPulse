"""
HTTP Health Checker Engine for CloudPulse.
Performs real HTTP probes, collects granular timing metrics (DNS, TCP, TLS, TTFB),
verifies status codes, and enforces strict SSRF safe-redirect controls.
"""

import time
import socket
import ssl
import urllib.parse
from typing import Dict, Any, Optional, Tuple
import requests

from .ssrf_guard import validate_target_url
from .models import Monitor, CheckResult


MAX_REDIRECTS = 5
DEFAULT_USER_AGENT = "CloudPulse-HealthChecker/1.0 (+https://cloudpulse.internal/bot)"


class SafeRedirectSession(requests.Session):
    """
    Custom requests Session that checks every redirect target URL against SSRF rules.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.max_redirects = MAX_REDIRECTS

    def rebuild_auth(self, prepared_request, response):
        # Validate next hop URL for SSRF
        is_valid, err_msg, _ = validate_target_url(prepared_request.url)
        if not is_valid:
            raise requests.exceptions.RequestException(f"Redirect blocked by SSRF Guard: {err_msg}")
        super().rebuild_auth(prepared_request, response)


def measure_socket_timings(url: str, timeout: float = 5.0) -> Tuple[float, float, Optional[str]]:
    """
    Measures DNS lookup time and TCP connect time via raw socket probe.
    Returns (dns_time_ms, connect_time_ms, resolved_ip).
    """
    parsed = urllib.parse.urlparse(url)
    hostname = parsed.hostname
    port = parsed.port or (443 if parsed.scheme == "https" else 80)

    dns_time_ms = 0.0
    connect_time_ms = 0.0
    resolved_ip = None

    # DNS timing
    t0 = time.perf_counter()
    try:
        addr_info = socket.getaddrinfo(hostname, port, proto=socket.IPPROTO_TCP)
        t1 = time.perf_counter()
        dns_time_ms = round((t1 - t0) * 1000, 2)
        if addr_info:
            resolved_ip = addr_info[0][4][0]
    except Exception:
        dns_time_ms = round((time.perf_counter() - t0) * 1000, 2)
        return dns_time_ms, 0.0, None

    # TCP Connect timing
    if resolved_ip:
        sock = socket.socket(socket.AF_INET if ":" not in resolved_ip else socket.AF_INET6, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        t_start_connect = time.perf_counter()
        try:
            sock.connect((resolved_ip, port))
            connect_time_ms = round((time.perf_counter() - t_start_connect) * 1000, 2)
        except Exception:
            connect_time_ms = round((time.perf_counter() - t_start_connect) * 1000, 2)
        finally:
            sock.close()

    return dns_time_ms, connect_time_ms, resolved_ip


def perform_health_check(monitor: Monitor, region: str = "us-east-1") -> CheckResult:
    """
    Executes a real HTTP health check against the monitor target URL.
    Enforces SSRF prevention, measures latency, checks status codes, and returns CheckResult.
    """
    # Step 1: Pre-validate URL against SSRF
    is_valid, err_msg, resolved_ips = validate_target_url(monitor.url)
    if not is_valid:
        return CheckResult(
            monitor_id=monitor.id,
            status="DOWN",
            status_code=None,
            latency_ms=0.0,
            dns_time_ms=0.0,
            connect_time_ms=0.0,
            ttfb_ms=0.0,
            error_message=f"SSRF Security Violation: {err_msg}",
            target_ip=resolved_ips[0] if resolved_ips else None,
            checked_from_region=region
        )

    # Step 2: Socket timings
    dns_ms, connect_ms, target_ip = measure_socket_timings(monitor.url, timeout=min(float(monitor.timeout_seconds), 5.0))
    if not target_ip and resolved_ips:
        target_ip = resolved_ips[0]

    # Step 3: Prepare HTTP request
    headers = {
        "User-Agent": DEFAULT_USER_AGENT,
        "Accept": "*/*",
        "Connection": "close"
    }
    if monitor.headers:
        headers.update(monitor.headers)

    session = SafeRedirectSession()
    method = (monitor.method or "GET").upper()
    timeout = max(1.0, float(monitor.timeout_seconds or 10))

    start_time = time.perf_counter()
    try:
        response = session.request(
            method=method,
            url=monitor.url,
            headers=headers,
            data=monitor.body if method in ("POST", "PUT", "PATCH") else None,
            timeout=timeout,
            allow_redirects=True,
            verify=True,
            stream=False
        )
        total_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
        ttfb_ms = round(response.elapsed.total_seconds() * 1000, 2)

        status_code = response.status_code
        expected = monitor.expected_status or 200

        # Status validation
        if status_code == expected:
            check_status = "UP"
            error = None
        else:
            check_status = "DOWN"
            error = f"HTTP status {status_code} does not match expected {expected}"

        # Capture response headers (selected safe headers)
        res_headers = {
            k: v for k, v in response.headers.items()
            if k.lower() in ("server", "content-type", "content-length", "date", "x-cache")
        }

        return CheckResult(
            monitor_id=monitor.id,
            status=check_status,
            status_code=status_code,
            latency_ms=total_time_ms,
            dns_time_ms=dns_ms,
            connect_time_ms=connect_ms,
            ttfb_ms=ttfb_ms,
            error_message=error,
            target_ip=target_ip,
            checked_from_region=region,
            headers=res_headers
        )

    except requests.exceptions.Timeout:
        latency = round((time.perf_counter() - start_time) * 1000, 2)
        return CheckResult(
            monitor_id=monitor.id,
            status="DOWN",
            status_code=None,
            latency_ms=latency,
            dns_time_ms=dns_ms,
            connect_time_ms=connect_ms,
            ttfb_ms=0.0,
            error_message=f"Request timed out after {timeout} seconds",
            target_ip=target_ip,
            checked_from_region=region
        )

    except requests.exceptions.SSLError as e:
        latency = round((time.perf_counter() - start_time) * 1000, 2)
        return CheckResult(
            monitor_id=monitor.id,
            status="DOWN",
            status_code=None,
            latency_ms=latency,
            dns_time_ms=dns_ms,
            connect_time_ms=connect_ms,
            ttfb_ms=0.0,
            error_message=f"TLS/SSL certificate error: {str(e)[:120]}",
            target_ip=target_ip,
            checked_from_region=region
        )

    except requests.exceptions.ConnectionError as e:
        latency = round((time.perf_counter() - start_time) * 1000, 2)
        return CheckResult(
            monitor_id=monitor.id,
            status="DOWN",
            status_code=None,
            latency_ms=latency,
            dns_time_ms=dns_ms,
            connect_time_ms=connect_ms,
            ttfb_ms=0.0,
            error_message=f"Connection failed: {str(e)[:120]}",
            target_ip=target_ip,
            checked_from_region=region
        )

    except Exception as e:
        latency = round((time.perf_counter() - start_time) * 1000, 2)
        return CheckResult(
            monitor_id=monitor.id,
            status="DOWN",
            status_code=None,
            latency_ms=latency,
            dns_time_ms=dns_ms,
            connect_time_ms=connect_ms,
            ttfb_ms=0.0,
            error_message=f"Check failed: {str(e)[:120]}",
            target_ip=target_ip,
            checked_from_region=region
        )
    finally:
        session.close()
