BEGIN;

-- Growth of metrics over time per repo

CREATE OR REPLACE VIEW repo_daily_growth AS 
SELECT 
    repo_id,
    snapshot_date,
    stars,
    stars - lag(stars) 
        OVER(
            PARTITION BY repo_id 
            ORDER BY snapshot_date
        ) AS star_growth
FROM repo_snapshots;

-- Total stars per company over time

CREATE OR REPLACE VIEW company_total_stars AS
SELECT 
    c.company_name,
    s.snapshot_date,
    SUM(s.stars) AS total_stars
FROM repo_snapshots s
JOIN repos r ON r.id = s.repo_id
JOIN companies c ON c.company_id = r.company_id
GROUP BY c.company_name, s.snapshot_date;

CREATE OR REPLACE VIEW current_repo_metrics AS
SELECT DISTINCT ON (repo_id)
    repo_id,
    snapshot_date,
    stars,
    forks,
    open_issues
FROM repo_snapshots
ORDER BY repo_id, snapshot_date DESC;

CREATE OR REPLACE VIEW current_repo_languages AS
SELECT DISTINCT ON (repo_id, language_id)
    repo_id,
    language_id,
    bytes
FROM language_snapshots
ORDER BY repo_id, language_id, snapshot_date DESC;

CREATE OR REPLACE VIEW top_languages AS
SELECT
    l.language_name,
    SUM(crl.bytes) AS total_bytes
FROM current_repo_languages crl
JOIN languages l ON l.language_id = crl.language_id
GROUP BY l.language_name
ORDER BY total_bytes DESC;

CREATE OR REPLACE VIEW top_repos_per_company AS
SELECT
    c.company_name,
    r.name AS repo_name,
    crm.stars
FROM current_repo_metrics crm
JOIN repos r ON r.id = crm.repo_id
JOIN companies c ON c.company_id = r.company_id
ORDER BY crm.stars DESC;

CREATE OR REPLACE VIEW language_popularity_by_company AS
SELECT
    c.company_name,
    l.language_name,
    SUM(crl.bytes) AS total_bytes
FROM current_repo_languages crl
JOIN repos r ON r.id = crl.repo_id
JOIN companies c ON c.company_id = r.company_id
JOIN languages l ON l.language_id = crl.language_id
GROUP BY c.company_name, l.language_name
ORDER BY c.company_name, total_bytes DESC;

CREATE OR REPLACE VIEW company_top_forked_repos AS
SELECT
    company_name,
    repo_name,
    forks
FROM (
    SELECT
        c.company_name,
        r.name AS repo_name,
        crm.forks,
        ROW_NUMBER() OVER (
            PARTITION BY c.company_name
            ORDER BY crm.forks DESC
        ) AS rank
    FROM current_repo_metrics crm
    JOIN repos r ON r.id = crm.repo_id
    JOIN companies c ON c.company_id = r.company_id
) ranked
WHERE rank <= 5
ORDER BY company_name, forks DESC;

CREATE OR REPLACE VIEW most_open_issues_repos AS
SELECT
    c.company_name,
    r.name AS repo_name,
    crm.open_issues
FROM current_repo_metrics crm
JOIN repos r ON r.id = crm.repo_id
JOIN companies c ON c.company_id = r.company_id
ORDER BY crm.open_issues DESC
LIMIT 10;

CREATE OR REPLACE VIEW company_largest_repos AS
SELECT
    company_name,
    repo_name,
    total_bytes
FROM (
    SELECT
        c.company_name,
        r.name AS repo_name,
        SUM(crl.bytes) AS total_bytes,
        ROW_NUMBER() OVER (
            PARTITION BY c.company_name
            ORDER BY SUM(crl.bytes) DESC
        ) AS rank
    FROM current_repo_languages crl
    JOIN repos r ON r.id = crl.repo_id
    JOIN companies c ON c.company_id = r.company_id
    GROUP BY c.company_name, r.name
) ranked
WHERE rank = 1;

CREATE OR REPLACE VIEW repo_activity_score AS
SELECT
    c.company_name,
    r.name AS repo_name,
    (crm.stars + crm.forks + crm.open_issues) AS activity_score
FROM current_repo_metrics crm
JOIN repos r ON r.id = crm.repo_id
JOIN companies c ON c.company_id = r.company_id
ORDER BY activity_score DESC;

CREATE OR REPLACE VIEW company_language_diversity AS
SELECT
    c.company_name,
    COUNT(DISTINCT crl.language_id) AS language_count
FROM current_repo_languages crl
JOIN repos r ON r.id = crl.repo_id
JOIN companies c ON c.company_id = r.company_id
GROUP BY c.company_name
ORDER BY language_count DESC;

COMMIT;