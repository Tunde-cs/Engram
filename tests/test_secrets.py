"""Tests for secret detection."""

from engram.secrets import scan_for_secrets


def test_detects_aws_access_key():
    assert scan_for_secrets("key is AKIAIOSFODNN7EXAMPLE") is not None


def test_detects_generic_sk_key():
    assert scan_for_secrets("use sk-abc123def456ghi789jkl012mno") is not None


def test_detects_jwt():
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
    assert scan_for_secrets(f"token: {token}") is not None


def test_detects_connection_string():
    assert scan_for_secrets("db = postgres://user:pass@host:5432/mydb") is not None


def test_detects_github_token():
    assert scan_for_secrets("GITHUB_TOKEN=ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghij") is not None


def test_clean_content_passes():
    assert scan_for_secrets("The auth service rate-limits to 1000 req/s per IP") is None


def test_clean_technical_content():
    assert scan_for_secrets("PostgreSQL 15.2 uses port 5432 with max_connections=200") is None
