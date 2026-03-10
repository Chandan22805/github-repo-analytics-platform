# GitHub Analytics Data Warehouse

A production-style GitHub analytics data warehouse featuring incremental ingestion, hybrid snapshot modeling, and automated daily pipelines.

This project demonstrates modern data engineering system design, including:

- Incremental API ingestion
- Hybrid event-driven + time-driven modeling
- Batch bulk loading
- State tracking
- Transactional integrity
- Automated orchestration
- Analytical warehouse design
- Data quality guarantees

---

# Architecture

## System Architecture
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
                       |                              
               +-------v--------+           
               | Analytical     |           
               | SQL Views      |            
               +-------+--------+            
                       |                          
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

---

# Data Pipeline Overview

The system follows a layered architecture:
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


This design cleanly separates:

- Data acquisition
- Warehouse modeling
- Analytical consumption

---

# Source Ingestion (Event-Driven)

The ingestion pipeline:

- Fetches only updated repository data using the `since` parameter
- Tracks ingestion state per company
- Uses idempotent inserts
- Uses batch loading (`execute_values`)
- Runs inside a single database transaction
- Avoids redundant API calls

Additional operational behavior:

- API retry with exponential backoff
- GitHub rate limit handling
- Structured pipeline logging

---

# Data Warehouse Modeling

## Dimension Tables

- `companies`
- `repos`
- `languages`

Dimensions store current metadata.

---

## Fact Tables

### Repository Metrics

`repo_snapshots`

Stores daily time-series metrics:

- stars
- forks
- open issues

Primary key:
(repo_id, snapshot_date)

---

### Language Distribution

`language_snapshots`

Stores historical language distribution per repository.

Primary key:
(repo_id, snapshot_date, language_id)


---

## Operational Tables

`ingestion_state`

Tracks the last successful ingestion timestamp per company and enables incremental API consumption.

---

# Hybrid Snapshot Strategy

This warehouse uses a hybrid modeling strategy.

### Event-Driven Ingestion

Only repositories updated since the last run are fetched from GitHub.

### Time-Driven Warehouse

Every ingestion run generates a daily snapshot for all tracked repositories.

| Repo Status | Snapshot Source |
|-------------|----------------|
Updated repo | Fresh API data |
Unchanged repo | Latest stored metrics |

Benefits:

- API efficiency
- deterministic daily time-series
- predictable compute load
- complete historical analytics

---

# Analytical Layer

Analytical views are defined in:
sql/views.sql


Examples:

### Repo Star Growth

`repo_daily_growth`

Uses window functions:
LAG(stars) OVER (PARTITION BY repo_id ORDER BY snapshot_date)


to calculate daily star growth.

---

### Company Metrics

`company_total_stars`

Aggregates repository metrics across companies.

---

These views support:

- time-series analytics
- trend analysis
- BI dashboards
- programmatic API queries

---

# Automation & Orchestration

The pipeline is automated using **GitHub Actions**.

Daily schedule:
cron: "0 2 * * *"


Pipeline steps:

1. Checkout repository
2. Install dependencies
3. Execute ingestion pipeline
4. Write results to Neon data warehouse

Manual execution is also supported using:
workflow_dispatch


---

# Data Quality & Operational Guarantees

The system enforces strong integrity guarantees.

## Database Constraints

- NOT NULL constraints
- Foreign keys
- Composite primary keys

## Idempotent Writes

All inserts use:
ON CONFLICT DO NOTHING


ensuring safe pipeline reruns.

## Snapshot Consistency

Each repository receives exactly:
1 snapshot per day


ensuring deterministic time-series data.

## Observability

Structured logs record:

- repositories processed
- snapshots written
- language distributions captured
- pipeline run summaries

---

# Project Structure

    root/
    │
    ├── sql/
    │ ├── schema.sql
    │ └── views.sql
    │
    ├── src/
    │ ├── config.py
    │ ├── db.py
    │ ├── github_client.py
    │ ├── ingest.py
    │ └── api.py
    │
    ├── .github/
    │ └── workflows/
    │ └── ingest.yml
    │
    ├── requirements.txt
    ├── Makefile
    ├── .gitignore
    └── README.md


---

# Running the System

## Setup database
make setup-db

## Run ingestion
make all

## Ingest a specific company
python src/ingest.py <GITHUB-USERNAME>

## Ingest all tracked companies
python src/ingest.py


---

# Key Design Decisions

## Hybrid Snapshot Modeling

GitHub repository metrics do not change frequently enough to justify full daily API pulls.

Hybrid modeling ensures efficient ingestion while maintaining complete historical analytics.

---

## Incremental API Consumption

Using GitHub's `since` parameter minimizes API usage and reduces pipeline runtime.

---

## Bulk Insert Strategy

Batch inserts reduce database round trips and improve ingestion performance when processing many repositories.

---

## State Tracking

The `ingestion_state` table enables reliable incremental ingestion and safe recovery after failures.

---

## Single Transaction Pipeline

Each pipeline run executes inside a single transaction.

This guarantees:

- atomic ingestion
- consistent warehouse updates
- no partial snapshots

---

# Future Improvements

Potential enhancements:

- Slowly Changing Dimensions (SCD)
- Partitioned fact tables
- Materialized analytical views
- Pipeline runtime monitoring

---

# Purpose

This project demonstrates:

- incremental data pipeline design
- warehouse modeling principles
- hybrid snapshot strategies
- transactional ingestion patterns
- automated data pipelines
- analytical warehouse design
- end-to-end data system thinking

The goal is to showcase data engineering architecture rather than simple API data extraction.
