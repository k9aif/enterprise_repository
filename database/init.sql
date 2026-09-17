-- ─────────────────────────────────────────────────────────────────────────────
-- k9x Enterprise Repository — Database Init
-- Run as: psql -U postgres -f init.sql
-- Creates schema enterprise_repository inside database enterprise_repository.
-- Safe to re-run: all statements use IF NOT EXISTS.
--
-- This is the TOGAF Architecture Repository counterpart to k9x_continuum
-- (which implements the Enterprise Continuum classification/governance layer).
-- entity_type/entity_id here are loose references to k9x_continuum's
-- sbbs/abbs tables (a different database on the same Postgres host) — no
-- cross-database FK is possible in Postgres, so referential integrity for
-- those pointers is enforced at the application layer, not the schema layer.
-- ─────────────────────────────────────────────────────────────────────────────

\connect enterprise_repository

CREATE SCHEMA IF NOT EXISTS enterprise_repository;
SET search_path TO enterprise_repository;

-- ─── Artifacts — actual content, not pointers ────────────────────────────────

CREATE TABLE IF NOT EXISTS enterprise_repository.artifacts (
    id              SERIAL          PRIMARY KEY,
    entity_type     VARCHAR(10)     NOT NULL,   -- 'sbb' | 'abb'
    entity_id       INTEGER         NOT NULL,   -- k9x_continuum.k9repo.{sbbs,abbs}.id
    entity_name     VARCHAR(255)    NOT NULL,   -- denormalized for display w/o cross-service call
    artifact_type   VARCHAR(50)     NOT NULL,
    -- 'source_code' | 'yaml_spec' | 'diagram_plantuml' | 'diagram_svg'
    -- | 'openapi_spec' | 'adr' | 'doc'
    filename        VARCHAR(255)    NOT NULL,
    mime_type       VARCHAR(100)    NOT NULL DEFAULT 'text/plain',
    content_text    TEXT,                       -- text artifacts (YAML, PlantUML, MD, JSON, code)
    content_bytes   BYTEA,                       -- small rendered binaries only (SVG/PNG)
    content_hash    VARCHAR(64)     NOT NULL,    -- sha256(content) — integrity + dedup
    size_bytes      INTEGER         NOT NULL,
    version         VARCHAR(20)     NOT NULL DEFAULT '1.0.0',
    git_ref         VARCHAR(500),
    captured_by     VARCHAR(255),
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    CONSTRAINT artifacts_content_check     CHECK (content_text IS NOT NULL OR content_bytes IS NOT NULL),
    CONSTRAINT artifacts_entity_type_check CHECK (entity_type IN ('sbb','abb'))
);

CREATE INDEX IF NOT EXISTS idx_artifacts_entity  ON enterprise_repository.artifacts (entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_hash    ON enterprise_repository.artifacts (content_hash);
CREATE INDEX IF NOT EXISTS idx_artifacts_type    ON enterprise_repository.artifacts (artifact_type);
CREATE INDEX IF NOT EXISTS idx_artifacts_created ON enterprise_repository.artifacts (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_artifacts_fts     ON enterprise_repository.artifacts
    USING GIN (to_tsvector('english', coalesce(entity_name,'') || ' ' || coalesce(content_text,'')));

-- ─── Standards Information Base ──────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS enterprise_repository.standards (
    id              SERIAL          PRIMARY KEY,
    name            VARCHAR(255)    NOT NULL,
    framework       VARCHAR(50)     NOT NULL,   -- 'TOGAF' | 'DoDAF' | 'MODAF' | 'NAF' | 'Custom'
    version         VARCHAR(20),
    mandatory       BOOLEAN         NOT NULL DEFAULT TRUE,
    description     TEXT,
    effective_date  DATE,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),

    CONSTRAINT standards_name_unique UNIQUE (name, framework)
);

CREATE INDEX IF NOT EXISTS idx_standards_framework ON enterprise_repository.standards (framework);

CREATE TABLE IF NOT EXISTS enterprise_repository.entity_standards (
    entity_type     VARCHAR(10)     NOT NULL,
    entity_id       INTEGER         NOT NULL,
    entity_name     VARCHAR(255)    NOT NULL,
    standard_id     INTEGER         NOT NULL REFERENCES enterprise_repository.standards(id) ON DELETE CASCADE,

    PRIMARY KEY (entity_type, entity_id, standard_id)
);

-- ─── Governance Log — real compliance data ───────────────────────────────────

CREATE TABLE IF NOT EXISTS enterprise_repository.compliance_assessments (
    id              SERIAL          PRIMARY KEY,
    entity_type     VARCHAR(10)     NOT NULL,
    entity_id       INTEGER         NOT NULL,
    entity_name     VARCHAR(255)    NOT NULL,
    criteria        TEXT            NOT NULL,
    verdict         VARCHAR(20)     NOT NULL,   -- 'pass' | 'fail' | 'conditional'
    assessor        VARCHAR(255)    NOT NULL,
    notes           TEXT,
    assessed_at     TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_assessments_entity ON enterprise_repository.compliance_assessments (entity_type, entity_id);

CREATE TABLE IF NOT EXISTS enterprise_repository.dispensations (
    id              SERIAL          PRIMARY KEY,
    entity_type     VARCHAR(10)     NOT NULL,
    entity_id       INTEGER         NOT NULL,
    entity_name     VARCHAR(255)    NOT NULL,
    standard_id     INTEGER         REFERENCES enterprise_repository.standards(id),
    reason          TEXT            NOT NULL,
    approver        VARCHAR(255)    NOT NULL,
    granted_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    expires_at      TIMESTAMPTZ     NOT NULL,
    status          VARCHAR(20)     NOT NULL DEFAULT 'active'  -- 'active' | 'expired' | 'revoked'
);

CREATE INDEX IF NOT EXISTS idx_dispensations_status ON enterprise_repository.dispensations (status, expires_at);
