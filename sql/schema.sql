BEGIN;

CREATE TABLE IF NOT EXISTS companies(
    company_id BIGINT PRIMARY KEY,
    company_name TEXT
);

CREATE TABLE IF NOT EXISTS repos(
    id BIGINT PRIMARY KEY,
    company_id BIGINT NOT NULL REFERENCES companies(company_id),
    name TEXT NOT NULL,
    full_name TEXT NOT NULL,
    language TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS repo_snapshots(
    repo_id BIGINT NOT NULL REFERENCES repos(id),
    snapshot_date DATE NOT NULL,
    stars BIGINT NOT NULL,
    forks BIGINT NOT NULL,
    open_issues INTEGER NOT NULL,
    PRIMARY KEY (repo_id, snapshot_date)
);

CREATE TABLE IF NOT EXISTS ingestion_state (
    source TEXT PRIMARY KEY,
    last_run TIMESTAMP
);

CREATE TABLE IF NOT EXISTS languages(
    language_id SERIAL PRIMARY KEY,
    language_name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS language_snapshots(
    repo_id BIGINT NOT NULL REFERENCES repos(id),
    snapshot_date DATE NOT NULL,
    language_id BIGINT NOT NULL REFERENCES languages(language_id),
    bytes BIGINT NOT NULL,
    PRIMARY KEY (repo_id, snapshot_date, language_id) 
);

COMMIT;