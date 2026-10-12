"""
Unit tests for SSRF Protection Guard.
Verifies blocking of private networks, AWS metadata, loopbacks, and safe acceptance of public URLs.
"""

import pytest
from backend.core.ssrf_guard import validate_target_url, is_ip_restricted
import ipaddress


def test_block_loopback_and_localhost():
    # Localhost
    valid, err, _ = validate_target_url("http://localhost:8000/api")
    assert not valid
    assert "Forbidden hostname" in err or "restricted" in err

    # 127.0.0.1
    valid, err, _ = validate_target_url("http://127.0.0.1:5000/metrics")
    assert not valid
    assert "forbidden" in err.lower() or "restricted" in err.lower()


def test_block_aws_metadata_service():
    # 169.254.169.254 is AWS Instance Metadata Service (IMDSv1 & IMDSv2)
    valid, err, _ = validate_target_url("http://169.254.169.254/latest/meta-data/")
    assert not valid
    assert "forbidden" in err.lower() or "restricted" in err.lower()


def test_block_private_rfc1918_addresses():
    # 10.0.0.0/8
    valid, err, _ = validate_target_url("http://10.1.2.3:8080/internal")
    assert not valid
    assert "forbidden" in err.lower() or "restricted" in err.lower()

    # 192.168.0.0/16
    valid, err, _ = validate_target_url("https://192.168.1.1/admin")
    assert not valid
    assert "forbidden" in err.lower() or "restricted" in err.lower()

    # 172.16.0.0/12
    valid, err, _ = validate_target_url("http://172.20.0.10/")
    assert not valid
    assert "forbidden" in err.lower() or "restricted" in err.lower()


def test_block_unspecified_and_multicast():
    valid, err, _ = validate_target_url("http://0.0.0.0:80")
    assert not valid

    valid, err, _ = validate_target_url("http://224.0.0.1:80")
    assert not valid


def test_block_invalid_schemes():
    valid, err, _ = validate_target_url("ftp://example.com/file")
    assert not valid
    assert "Invalid protocol" in err

    valid, err, _ = validate_target_url("file:///etc/passwd")
    assert not valid
    assert "Invalid protocol" in err

    valid, err, _ = validate_target_url("gopher://example.com")
    assert not valid


def test_accept_public_ip_and_domain():
    # Google DNS public IP
    valid, err, ips = validate_target_url("https://8.8.8.8")
    assert valid
    assert "8.8.8.8" in ips

    # Cloudflare public IP
    valid, err, ips = validate_target_url("https://1.1.1.1")
    assert valid
    assert "1.1.1.1" in ips

    # Public domain
    valid, err, ips = validate_target_url("https://dns.google")
    assert valid
    assert len(ips) > 0
