# GitHub Analytics Data Warehouse

A production-style GitHub analytics data warehouse featuring incremental ingestion, hybrid snapshot modeling, automated daily pipelines, and comprehensive test coverage.

This project demonstrates modern data engineering system design, including:

- Incremental API ingestion with state tracking
- Hybrid event-driven + time-driven snapshot modeling
- Batch bulk loading with idempotent writes
- Two-phase ingestion pipeline (read → process → write)
- Transactional integrity and atomic commits
- Automated orchestration via GitHub Actions
- Analytical warehouse design with SQL views
- Data quality guarantees and schema constraints
- Comprehensive unit and integration tests

---

# Architecture

## System Architecture

```
            +----------------------+
            |      GitHub API      |
            +----------+-----------+
                       |
                       | Incremental Fetch (since)
                       |
                +------v------+
                |  Ingestion  |
                |  Pipeline   |
                |  (Python)   |
                +------+------+
                       |
                       | Bulk Inserts
                       |
             +---------v----------+
             |  Neon PostgreSQL   |
             |  Data Warehouse    |
             +---------+----------+
                       |
                       |
               +-------v--------+
               | Analytical     |
               | SQL Views      |
               +-------+--------+
                       |
               +-------v--------+
               |  BI Dashboard  |
               +----------------+
                       ^
                       |
              +--------+--------+
              | GitHub Actions  |
              | Daily Scheduler |
              +-----------------+
```

---

# Data Pipeline Overview

The system follows a layered architecture:

```
GitHub API
    ↓
Incremental Ingestion (Event-Driven)
    ↓
Dimension Tables
    ↓
Daily Snapshot Layer (Time-Driven)
    ↓
Analytical Views
    ↓
Dashboards / API Consumers
```

This design cleanly separates:

- Data acquisition
- Warehouse modeling
- Analytical consumption

---

# Two-Phase Ingestion Architecture

The pipeline is split into two distinct phases to handle long-running API operations efficiently:

## Phase I: Read State (Database Connection #1)

Executed synchronously at pipeline start:
- Fetch last run timestamp per company from `ingestion_state`
- Retrieve latest repository metrics from `repo_snapshots`
- Retrieve latest language metrics from `language_snapshots`
- Fetch list of companies to process
- Close connection immediately after

This phase completes in seconds. The connection is closed before the long-running API phase to avoid timeout issues with Neon's connection suspension on idle databases.

## Phase II: API Calls + Write (Database Connection #2)

Long-running phase with no database activity:
- Iterate through all companies
- For each company, fetch repos updated since last run using `since` parameter
- For each updated repo, fetch language distribution from GitHub API
- Build in-memory data structures (lists, dicts) for all entities
- After API phase completes, establish new database connection
- Execute all writes in a single transaction
- Cleanup old snapshots (30+ days)
- Commit transaction atomically

This two-phase design:
- **Solves connection suspension**: Neon suspends idle connections after ~5 minutes. By closing Phase I immediately, we avoid the timeout during the long API phase.
- **Maintains transactional guarantees**: All writes happen in Phase III as a single atomic transaction.
- **Scales with data volume**: The 13k+ repos × long-running API calls scenario is handled gracefully.

---

# Source Ingestion (Event-Driven)

The ingestion pipeline:

- Fetches only updated repository data using GitHub's `since` parameter
- Tracks ingestion state per company in `ingestion_state` table
- Uses idempotent inserts with `ON CONFLICT DO NOTHING`
- Uses batch loading via `execute_values()` for efficiency
- Runs all writes inside a single database transaction
- Avoids redundant API calls for unchanged repositories

Additional operational behavior:

- API retry with exponential backoff (2^attempt seconds)
- GitHub rate limit handling and sleep on throttle
- Structured logging of pipeline execution
- Automatic cleanup of snapshots older than 30 days

---

# Data Warehouse Modeling

## Dimension Tables

**`companies`** — stores company metadata and tracking info
- company_id (PK)
- company_name

**`repos`** — stores repository metadata
- id (PK)
- company_id (FK)
- name, full_name, language
- created_at, updated_at

**`languages`** — stores unique programming languages
- language_id (PK)
- language_name (UNIQUE)

---

## Fact Tables

### Repository Metrics (`repo_snapshots`)

Stores daily time-series metrics for each repository:
- repo_id (FK)
- snapshot_date
- stars, forks, open_issues

Primary key: `(repo_id, snapshot_date)` — one snapshot per repository per day

---

### Language Distribution (`language_snapshots`)

Stores historical language composition per repository:
- repo_id (FK)
- snapshot_date
- language_id (FK)
- bytes (lines of code in that language)

Primary key: `(repo_id, snapshot_date, language_id)`

---

## Operational Tables

**`ingestion_state`** — tracks incremental ingestion progress
- source (company username) — PK
- last_run (timestamp of last successful ingestion)

Enables reliable incremental API consumption and safe recovery after failures.

---

# Hybrid Snapshot Strategy

This warehouse uses a hybrid modeling strategy optimizing for both API efficiency and analytical completeness.

## Event-Driven Ingestion

Only repositories updated since the last run are fetched from GitHub. Uses the `since` parameter to minimize API calls — daily delta is typically a few hundred repos for stable organizations like Google, Meta, Apple.

## Time-Driven Warehouse

Every ingestion run generates a daily snapshot for **all tracked repositories**, not just changed ones:

| Repo Status | Snapshot Source |
|-------------|----------------|
| Updated repo | Fresh API data |
| Unchanged repo | Latest stored metrics (reused) |

Benefits:

- **API efficiency** — avoid redundant calls for stable repos
- **Deterministic time-series** — guaranteed one snapshot per repo per day
- **Predictable compute load** — snapshot count is fixed daily
- **Complete historical analytics** — no gaps in time-series data

---

# Analytical Layer

Analytical views are defined in `sql/views.sql` and support real-time BI dashboards and programmatic queries.

### Examples

**`repo_daily_growth`** — calculates daily star growth using window functions
```sql
LAG(stars) OVER (PARTITION BY repo_id ORDER BY snapshot_date)
```

**`company_total_stars`** — aggregates repository metrics across all repos per company

**`language_popularity_by_company`** — shows programming language distribution and trends per company

**`company_top_forked_repos`** — ranks repositories by forks within each company

**`repo_activity_score`** — composite metric combining stars, forks, and open issues

These views support:
- Time-series analytics and trend analysis
- BI dashboards and ad-hoc queries
- Programmatic API access to aggregated data

---

# Automation & Orchestration

The pipeline is automated using **GitHub Actions** with daily scheduling.

### Workflow Configuration

```yaml
schedule:
  - cron: "0 2 * * *"  # Runs every day at 02:00 UTC
workflow_dispatch:     # Manual trigger available
```

### Pipeline Steps

1. Checkout repository
2. Set up Python 3.11
3. Install dependencies from `requirements.txt`
4. Execute ingestion pipeline (`src/ingest.py`)
5. Write results to Neon PostgreSQL data warehouse

All logs are captured by GitHub Actions and retained for 90 days, visible in the Actions tab of the repository.

---

# Testing

Comprehensive test suite covering unit tests for database operations and integration tests for the ingestion pipeline.

## Test Structure

**`tests/test_db.py`** — unit tests for database layer
- Read operations: `get_last_run`, `get_all_companies`, `get_latest_repo_metrics`, `get_latest_language_metrics`, `get_all_languages`
- Write operations: `bulk_insert_*` functions
- Cleanup operations: `clean_up_db`
- Tests for both empty and non-empty inputs

**`tests/test_ingest.py`** — integration tests for the ingestion pipeline
- Empty company list handling
- Non-empty ingestion with mock GitHub API
- Error handling: missing repos, missing fields, missing languages
- Cleanup function invocation

**`tests/conftest.py`** — pytest fixtures shared across tests
- `mock_conn` — mocked database connection
- `mock_github_client` — mocked GitHub API client

## Running Tests

```bash
pytest tests/
pytest tests/test_db.py          # Only database tests
pytest tests/test_ingest.py      # Only pipeline tests
pytest tests/ -v                 # Verbose output
```

All tests use mocking to avoid external dependencies:
- Database operations are mocked with `unittest.mock.MagicMock`
- GitHub API calls are mocked
- `execute_values` is patched to prevent actual DB writes

---

# Data Quality & Operational Guarantees

The system enforces strong integrity and consistency guarantees.

## Database Constraints

- NOT NULL constraints on critical fields
- Foreign key relationships between all fact and dimension tables
- Composite primary keys ensuring uniqueness of daily snapshots
- UNIQUE constraints on language names

## Idempotent Writes

All inserts use `ON CONFLICT DO NOTHING`:
```sql
INSERT INTO repo_snapshots(...) VALUES %s
ON CONFLICT (repo_id, snapshot_date) DO NOTHING;
```

This ensures safe pipeline reruns — re-executing the same day's ingestion is harmless.

## Snapshot Consistency

Each repository receives exactly one snapshot per day, ensuring:
- Deterministic time-series data
- No duplicate snapshots
- Predictable row counts

## Automated Cleanup

The `clean_up_db()` function runs daily to delete snapshots older than 30 days, keeping storage capped at ~150 MB on Neon's free tier while maintaining sufficient history for trend analysis.

## Observability

Structured logs record:
- Companies processed and count
- Repositories updated
- Snapshots written
- Language distributions captured
- Pipeline run duration
- Phase completion status

---

# Project Structure

```
root/
│
├── sql/
│   ├── schema.sql          # Table definitions and constraints
│   └── views.sql           # Analytical views
│
├── src/
│   ├── config.py           # Environment and configuration
│   ├── db.py               # Database operations (reads + writes)
│   ├── github_client.py    # GitHub API client with retry logic
│   ├── ingest.py           # Two-phase ingestion orchestration
│   └── api.py              # GitHub API reference
│
├── tests/
│   ├── conftest.py         # Pytest fixtures
│   ├── test_db.py          # Database operation tests
│   └── test_ingest.py      # Pipeline integration tests
│
├── .github/
│   └── workflows/
│       └── ingest.yml      # GitHub Actions daily scheduler
│
├── requirements.txt        # Python dependencies
├── Makefile                # Local development commands
├── .gitignore              # Git ignore rules
└── README.md               # This file
```
---

# Future Improvements

Potential enhancements for this project:

- **Orchestration** — migrate from GitHub Actions to Apache Airflow or Prefect for more sophisticated scheduling, error handling, and task dependencies
- **Materialized Views** — pre-compute expensive aggregations for dashboard performance
- **Pipeline Monitoring** — integrate with observability platforms (Datadog, New Relic) for alerting on failures and performance degradation
- **dbt Integration** — move SQL transformations to dbt for version control, testing, and documentation of the analytics layer

---

# Purpose

This project demonstrates:

- Incremental data pipeline design and optimization
- Warehouse modeling principles (facts, dimensions, slowly changing data)
- Hybrid snapshot strategies for balancing efficiency and completeness
- Transactional ingestion patterns and ACID guarantees
- Automated data pipelines via CI/CD (GitHub Actions)
- Analytical warehouse design with performant queries
- End-to-end data system thinking from source to analytics
- Comprehensive testing for data pipelines

The goal is to showcase data engineering architecture.
