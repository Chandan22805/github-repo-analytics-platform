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
