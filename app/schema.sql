CREATE TABLE IF NOT EXISTS publishers (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS tags (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS themes (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS games (
    app_id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    profile_text TEXT NOT NULL,
    profile_version INTEGER NOT NULL,
    features JSONB NOT NULL,
    language TEXT NOT NULL,
    source_url TEXT NOT NULL,
    fetched_at TIMESTAMPTZ NOT NULL,
    verification TEXT NOT NULL CHECK (verification IN ('verified', 'inferred')),
    provenance TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS game_publishers (
    app_id INTEGER NOT NULL REFERENCES games (app_id) ON DELETE CASCADE,
    publisher_id INTEGER NOT NULL REFERENCES publishers (id),
    source_url TEXT NOT NULL,
    fetched_at TIMESTAMPTZ NOT NULL,
    verification TEXT NOT NULL CHECK (verification IN ('verified', 'inferred')),
    PRIMARY KEY (app_id, publisher_id)
);

CREATE TABLE IF NOT EXISTS game_tags (
    app_id INTEGER NOT NULL REFERENCES games (app_id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES tags (id),
    source_url TEXT NOT NULL,
    fetched_at TIMESTAMPTZ NOT NULL,
    verification TEXT NOT NULL CHECK (verification IN ('verified', 'inferred')),
    PRIMARY KEY (app_id, tag_id)
);

CREATE TABLE IF NOT EXISTS evidence (
    id TEXT PRIMARY KEY,
    app_id INTEGER NOT NULL REFERENCES games (app_id) ON DELETE CASCADE,
    verdict TEXT NOT NULL CHECK (verdict IN ('positive', 'negative')),
    body TEXT NOT NULL,
    helpful BOOLEAN NOT NULL,
    recent BOOLEAN NOT NULL,
    off_topic BOOLEAN NOT NULL DEFAULT FALSE,
    language TEXT NOT NULL,
    source_label TEXT NOT NULL CHECK (source_label IN ('synthetic_fixture', 'steam_review')),
    source_url TEXT,
    fetched_at TIMESTAMPTZ NOT NULL,
    CHECK (source_label <> 'synthetic_fixture' OR body LIKE 'SYNTHETIC FIXTURE — %')
);

CREATE INDEX IF NOT EXISTS evidence_app_id_idx ON evidence (app_id);

CREATE TABLE IF NOT EXISTS game_themes (
    app_id INTEGER NOT NULL REFERENCES games (app_id) ON DELETE CASCADE,
    theme_id INTEGER NOT NULL REFERENCES themes (id),
    support TEXT NOT NULL CHECK (support IN ('supports', 'contradicts')),
    evidence_ids TEXT[] NOT NULL,
    sample_size INTEGER NOT NULL,
    language TEXT NOT NULL,
    fetched_at TIMESTAMPTZ NOT NULL,
    verification TEXT NOT NULL CHECK (verification IN ('verified', 'inferred')),
    PRIMARY KEY (app_id, theme_id, support)
);

CREATE TABLE IF NOT EXISTS media_assets (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    app_id INTEGER NOT NULL REFERENCES games (app_id) ON DELETE CASCADE,
    kind TEXT NOT NULL,
    source_url TEXT,
    approved BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS index_jobs (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    app_id INTEGER NOT NULL,
    op TEXT NOT NULL CHECK (op IN ('upsert', 'delete')),
    profile_version INTEGER NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'running', 'done', 'failed')),
    attempts INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    acked_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS index_jobs_pending_idx ON index_jobs (id) WHERE status = 'pending';
