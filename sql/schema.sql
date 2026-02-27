BEGIN;

CREATE TABLE IF NOT EXISTS companies(
    company_id BIGINT PRIMARY KEY,
    company_name TEXT
);

CREATE TABLE IF NOT EXISTS repos(
    id BIGINT PRIMARY KEY,
    company_id BIGINT REFERENCES companies(company_id)
    name TEXT,
    full_name TEXT,
    language TEXT,
    created_at TIMESTAMP,
    update_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS repo_sanpshots(
    repo_id BIGINT REFERENCES repos(id),
    snapshot_date DATE,
    stars BIGINT,
    forks BIGINT,
    open_issues INTEGER,
    PRIMARY KEY (repo_id, snapshot_date)
);

COMMIT;