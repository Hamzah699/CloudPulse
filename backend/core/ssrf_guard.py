"""
SSRF Protection Module for CloudPulse.
Validates URLs against private network access, AWS metadata endpoints (169.254.169.254),
loopback, bogon, link-local, and unauthorized internal IP ranges.
"""

import ipaddress
import socket
import urllib.parse
from typing import Tuple, List, Optional


DISALLOWED_HOSTNAMES = {
    "localhost",
    "localhost.localdomain",
    "ip6-localhost",
    "ip6-loopback",
    "metadata.google.internal",
    "instance-data",
}

# Additional custom restricted IP networks
EXTRA_RESTRICTED_NETWORKS = [
    ipaddress.ip_network("100.64.0.0/10"),     # Carrier-grade NAT
    ipaddress.ip_network("198.18.0.0/15"),     # Network benchmark tests
    ipaddress.ip_network("192.0.0.0/24"),      # IETF Protocol Assignments
    ipaddress.ip_network("192.0.2.0/24"),      # Documentation TEST-NET-1
    ipaddress.ip_network("198.51.100.0/24"),   # Documentation TEST-NET-2
    ipaddress.ip_network("203.0.113.0/24"),    # Documentation TEST-NET-3
    ipaddress.ip_network("240.0.0.0/4"),       # Reserved for future use
    ipaddress.ip_network("255.255.255.255/32"),# Broadcast
    ipaddress.ip_network("169.254.0.0/16"),    # Link-local / AWS EC2 & ECS Instance Metadata
]


class SSRFValidationError(ValueError):
    """Raised when a URL fails SSRF safety checks."""
    pass


def is_ip_restricted(ip_obj: ipaddress.IPv4Address | ipaddress.IPv6Address) -> Tuple[bool, str]:
    """Check if an IP address belongs to any restricted or private block."""
    if ip_obj.is_loopback:
        return True, "Loopback address (127.0.0.0/8 or ::1)"
    if ip_obj.is_private:
        return True, "Private RFC1918 or RFC4193 network address"
    if ip_obj.is_link_local:
        return True, "Link-local address (including 169.254.169.254 AWS metadata)"
    if ip_obj.is_multicast:
        return True, "Multicast address"
    if ip_obj.is_reserved:
        return True, "Reserved IP address"
    if ip_obj.is_unspecified:
        return True, "Unspecified address (0.0.0.0 or ::)"

    # Check extra custom restricted networks
    for net in EXTRA_RESTRICTED_NETWORKS:
        if ip_obj in net:
            return True, f"Restricted network block ({net})"

    return False, ""


def validate_target_url(url: str, allow_custom_ports: bool = True) -> Tuple[bool, str, List[str]]:
    """
    Validates a target monitor URL for SSRF vulnerabilities.
    
    Returns:
        (is_valid: bool, error_message: str, resolved_ips: List[str])
    """
    if not url or not isinstance(url, str):
        return False, "URL must be a non-empty string", []

    url = url.strip()
    if len(url) > 2048:
        return False, "URL length exceeds maximum permitted 2048 characters", []

    try:
        parsed = urllib.parse.urlparse(url)
    except Exception as e:
        return False, f"Malformed URL syntax: {str(e)}", []

    # 1. Scheme check
    scheme = (parsed.scheme or "").lower()
    if scheme not in ("http", "https"):
        return False, f"Invalid protocol '{scheme}'. Only http:// and https:// are allowed.", []

    # 2. Hostname check
    hostname = parsed.hostname
    if not hostname:
        return False, "Missing hostname in URL", []

    hostname_lower = hostname.lower()
    if hostname_lower in DISALLOWED_HOSTNAMES:
        return False, f"Forbidden hostname '{hostname}'", []

    if hostname_lower.endswith(".local") or hostname_lower.endswith(".internal"):
        return False, f"Internal domain zone '{hostname}' is not permitted", []

    # 3. Port check
    port = parsed.port
    if port is None:
        port = 443 if scheme == "https" else 80
    else:
        if port <= 0 or port > 65535:
            return False, f"Port {port} out of range (1-65535)", []
        if not allow_custom_ports and port not in (80, 443, 8080, 8443):
            return False, f"Custom port {port} is not permitted", []

    # 4. Resolve hostname to all IP addresses
    resolved_ips: List[str] = []
    try:
        # Check if hostname is already a raw IP literal
        try:
            ip_obj = ipaddress.ip_address(hostname)
            is_restr, reason = is_ip_restricted(ip_obj)
            if is_restr:
                return False, f"Direct IP '{hostname}' is forbidden: {reason}", [str(ip_obj)]
            resolved_ips.append(str(ip_obj))
        except ValueError:
            # Hostname is a domain name -> DNS resolution
            addr_info = socket.getaddrinfo(hostname, port, proto=socket.IPPROTO_TCP)
            if not addr_info:
                return False, f"Could not resolve domain '{hostname}'", []

            for item in addr_info:
                sockaddr = item[4]
                ip_str = sockaddr[0]
                resolved_ips.append(ip_str)

                try:
                    ip_obj = ipaddress.ip_address(ip_str)
                    is_restr, reason = is_ip_restricted(ip_obj)
                    if is_restr:
                        return False, f"Hostname '{hostname}' resolves to restricted IP {ip_str}: {reason}", resolved_ips
                except ValueError:
                    return False, f"Resolved IP {ip_str} is invalid", resolved_ips

    except socket.gaierror as e:
        return False, f"DNS resolution failed for '{hostname}': {e.strerror}", []
    except Exception as e:
        return False, f"Network validation error: {str(e)}", []

    # Deduplicate resolved IPs
    unique_ips = list(dict.fromkeys(resolved_ips))
    return True, "", unique_ips
