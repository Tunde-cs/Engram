"""Tests for the storage layer."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

import pytest

from engram.storage import Storage


@pytest.mark.asyncio
async def test_insert_and_retrieve_fact(storage: Storage):
    fact_id = uuid.uuid4().hex
    now = datetime.now(timezone.utc).isoformat()
    fact = {
        "id": fact_id,
        "lineage_id": uuid.uuid4().hex,
        "content": "The auth service rate-limits to 1000 req/s",
        "content_hash": "abc123",
        "scope": "auth",
        "confidence": 0.9,
        "fact_type": "observation",
        "agent_id": "agent-1",
        "engineer": "alice",
        "provenance": "src/auth.py:42",
        "keywords": json.dumps(["auth", "rate-limit"]),
        "entities": json.dumps([{"name": "rate_limit", "type": "numeric", "value": 1000}]),
        "artifact_hash": None,
        "embedding": b"\x00" * 16,
        "embedding_model": "all-MiniLM-L6-v2",
        "embedding_ver": "3.0.0",
        "committed_at": now,
        "valid_from": now,
        "valid_until": None,
        "ttl_days": None,
    }
    await storage.insert_fact(fact)

    retrieved = await storage.get_fact_by_id(fact_id)
    assert retrieved is not None
    assert retrieved["content"] == "The auth service rate-limits to 1000 req/s"
    assert retrieved["scope"] == "auth"


@pytest.mark.asyncio
async def test_dedup_check(storage: Storage):
    now = datetime.now(timezone.utc).isoformat()
    fact = {
        "id": uuid.uuid4().hex,
        "lineage_id": uuid.uuid4().hex,
        "content": "test fact",
        "content_hash": "dedup_hash_123",
        "scope": "test",
        "confidence": 0.8,
        "fact_type": "observation",
        "agent_id": "agent-1",
        "engineer": None,
        "provenance": None,
        "keywords": "[]",
        "entities": "[]",
        "artifact_hash": None,
        "embedding": None,
        "embedding_model": "test",
        "embedding_ver": "1.0",
        "committed_at": now,
        "valid_from": now,
        "valid_until": None,
        "ttl_days": None,
    }
    await storage.insert_fact(fact)

    dup = await storage.find_duplicate("dedup_hash_123", "test")
    assert dup == fact["id"]

    no_dup = await storage.find_duplicate("different_hash", "test")
    assert no_dup is None
