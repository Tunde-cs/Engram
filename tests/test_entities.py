"""Tests for entity extraction."""

from engram.entities import extract_entities, extract_keywords


def test_extracts_numeric_with_unit():
    entities = extract_entities("The auth service rate-limits to 1000 req/s per IP")
    numerics = [e for e in entities if e["type"] == "numeric"]
    assert len(numerics) >= 1
    assert any(e["value"] == 1000 for e in numerics)


def test_extracts_config_key():
    entities = extract_entities("configured via AUTH_RATE_LIMIT in .env")
    config_keys = [e for e in entities if e["type"] == "config_key"]
    assert any(e["name"] == "AUTH_RATE_LIMIT" for e in config_keys)


def test_extracts_service_name():
    entities = extract_entities("the auth service handles JWT refresh")
    services = [e for e in entities if e["type"] == "service"]
    assert any(e["name"] == "auth" for e in services)


def test_extracts_technology():
    entities = extract_entities("We use PostgreSQL 15.2 for the main database")
    techs = [e for e in entities if e["type"] == "technology"]
    assert any(e["name"] == "postgresql" for e in techs)


def test_extracts_version():
    entities = extract_entities("Running Redis version 7.2.4")
    versions = [e for e in entities if e["type"] == "version"]
    assert any(e["value"] == "7.2.4" for e in versions)


def test_extracts_port():
    entities = extract_entities("PostgreSQL runs on port 5432")
    numerics = [e for e in entities if e["type"] == "numeric"]
    assert any(e["value"] == 5432 for e in numerics)


def test_keywords_extraction():
    keywords = extract_keywords("The auth service rate-limits to 1000 req/s per IP")
    assert "auth" in keywords
    assert "service" in keywords


def test_empty_content():
    assert extract_entities("") == []
    assert extract_keywords("") == []
