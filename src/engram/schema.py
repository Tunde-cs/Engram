"""Phase 1 — Database schema and migrations for Engram.

Every fact carries a temporal validity window (valid_from, valid_until).
Supersession, correction, archival, and versioning are all expressed
through this single primitive.
"""

SCHEMA_VERSION = 1

SCHEMA_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA busy_timeout=5000;
PRAGMA foreign_keys=ON;

-- Core fact store: append-only, bitemporal
CREATE TABLE IF NOT EXISTS facts (
    id               TEXT PRIMARY KEY,
    lineage_id       TEXT NOT NULL,
    content          TEXT NOT NULL,
    content_hash     TEXT NOT NULL,
    scope            TEXT NOT NULL,
    confidence       REAL NOT NULL,
    fact_type        TEXT NOT NULL DEFAULT 'observation',
    agent_id         TEXT NOT NULL,
    engineer         TEXT,
    provenance       TEXT,
    keywords         TEXT,       -- JSON array
    entities         TEXT,       -- JSON array: [{name, type, value}, ...]
    artifact_hash    TEXT,
    embedding        BLOB,
    embedding_model  TEXT NOT NULL,
    embedding_ver    TEXT NOT NULL,
    committed_at     TEXT NOT NULL,
    valid_from       TEXT NOT NULL,
    valid_until      TEXT,
    ttl_days         INTEGER
);

CREATE INDEX IF NOT EXISTS idx_facts_validity     ON facts(scope, valid_until);
CREATE INDEX IF NOT EXISTS idx_facts_content_hash ON facts(content_hash);
CREATE INDEX IF NOT EXISTS idx_facts_lineage      ON facts(lineage_id);
CREATE INDEX IF NOT EXISTS idx_facts_agent        ON facts(agent_id);
CREATE INDEX IF NOT EXISTS idx_facts_type         ON facts(fact_type);

-- FTS5 for lexical retrieval (replaces rank_bm25 dependency)
CREATE VIRTUAL TABLE IF NOT EXISTS facts_fts USING fts5(
    content, scope, keywords,
    content=facts, content_rowid=rowid
);

-- Triggers to keep FTS5 in sync
CREATE TRIGGER IF NOT EXISTS facts_ai AFTER INSERT ON facts BEGIN
    INSERT INTO facts_fts(rowid, content, scope, keywords)
    VALUES (new.rowid, new.content, new.scope, new.keywords);
END;

CREATE TRIGGER IF NOT EXISTS facts_ad AFTER DELETE ON facts BEGIN
    INSERT INTO facts_fts(facts_fts, rowid, content, scope, keywords)
    VALUES ('delete', old.rowid, old.content, old.scope, old.keywords);
END;

-- Conflict tracking
CREATE TABLE IF NOT EXISTS conflicts (
    id               TEXT PRIMARY KEY,
    fact_a_id        TEXT NOT NULL REFERENCES facts(id),
    fact_b_id        TEXT NOT NULL REFERENCES facts(id),
    detected_at      TEXT NOT NULL,
    detection_tier   TEXT NOT NULL,
    nli_score        REAL,
    explanation      TEXT,
    severity         TEXT NOT NULL,
    status           TEXT NOT NULL DEFAULT 'open',
    resolved_by      TEXT,
    resolved_at      TEXT,
    resolution       TEXT,
    resolution_type  TEXT
);

CREATE INDEX IF NOT EXISTS idx_conflicts_status ON conflicts(status);
CREATE INDEX IF NOT EXISTS idx_conflicts_fact_a ON conflicts(fact_a_id);
CREATE INDEX IF NOT EXISTS idx_conflicts_fact_b ON conflicts(fact_b_id);

-- Agent registry
CREATE TABLE IF NOT EXISTS agents (
    agent_id         TEXT PRIMARY KEY,
    engineer         TEXT NOT NULL,
    label            TEXT,
    registered_at    TEXT NOT NULL,
    last_seen        TEXT,
    total_commits    INTEGER DEFAULT 0,
    flagged_commits  INTEGER DEFAULT 0
);

-- NLI feedback for threshold calibration
CREATE TABLE IF NOT EXISTS detection_feedback (
    conflict_id    TEXT NOT NULL REFERENCES conflicts(id),
    feedback       TEXT NOT NULL,
    recorded_at    TEXT NOT NULL
);

-- Scope-level permissions (temporal)
CREATE TABLE IF NOT EXISTS scope_permissions (
    agent_id    TEXT NOT NULL,
    scope       TEXT NOT NULL,
    can_read    INTEGER NOT NULL DEFAULT 1,
    can_write   INTEGER NOT NULL DEFAULT 1,
    valid_from  TEXT,
    valid_until TEXT,
    PRIMARY KEY (agent_id, scope)
);

-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""
