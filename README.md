# GitHub Analytics Data Warehouse

A production-style incremental GitHub analytics data warehouse featuring hybrid snapshot modeling, batch ingestion, and time-series analysis.

This project demonstrates data engineering maturity through:

- Incremental API ingestion
- Hybrid event-driven + time-driven modeling
- Batch bulk loading
- State tracking
- Transactional integrity
- Analytical warehouse design

---

## Architecture Overview

The system is built in layered form:

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
```

---

## Source Ingestion (Event-Driven)

- Fetches only updated repository data using `since`
- Tracks ingestion state per company
- Uses idempotent inserts
- Uses bulk batch loading (`execute_values`)
- Single transaction per ingestion run
- Efficient API usage (no redundant calls)

---

## Warehouse Modeling

### Dimension Tables

- `companies`
- `repos`

### Fact Table

- `repo_snapshots`

### Additional Tables

- `ingestion_state`

### Design Characteristics

- Daily snapshot generation independent of API updates
- Separation of ingestion logic from analytical modeling
- Deterministic time-series grid
- Referential integrity enforced via foreign keys

---

## Hybrid Snapshot Design

This project uses a hybrid modeling strategy:

### Event-Driven Ingestion
Only repositories updated since the last run are fetched from GitHub.

### Time-Driven Warehouse
Every run generates a daily snapshot for all tracked repositories:
- Updated repositories use fresh API data
- Unchanged repositories reuse latest stored metrics
- Ensures one row per repo per day
- Avoids unnecessary API usage

This approach provides:

- API efficiency
- Predictable compute load
- Strong time-series modeling capability
- Clear separation of concerns

---

## Analytical Layer

Analytical views are defined in `views.sql`.

Examples:

- `repo_daily_growth` (LAG-based star growth)
- `company_total_stars` (aggregated company metrics)

Features:

- Window functions (LAG for growth calculation)
- Aggregation views
- Structured time-series queries
- Ready for BI tools or dashboard integration

---

## Operational Guarantees

- Idempotent ingestion
- Deterministic daily snapshots
- Atomic transaction per run
- No redundant API calls
- Consistent state tracking

---

## Project Structure

```
root/
│
├── sql/
│   ├── schema.sql
│   └── views.sql
│
├── src/
│   ├── config.py
│   ├── db.py
│   ├── github_client.py
│   └── ingest.py
│
├── requirements.txt
├── .gitignore
├── Makefile
└── README.md
```

---

## How to Run

1. Start PostgreSQL
2. Run database setup:

```
make setup-db
```

3. Run ingestion:

```
make all
```

To ingest a specific company:

```
python src/ingest.py <company_name>
```

To ingest all tracked companies:

```
python src/ingest.py
```

---

## Design Decisions

### 1. Hybrid Snapshot Modeling
GitHub metrics do not change frequently enough to justify full daily API pulls.  
Incremental ingestion ensures API efficiency, while daily snapshot generation ensures analytical completeness.

### 2. Bulk Inserts
Bulk loading reduces database round-trips and improves ingestion performance when handling many repositories.

### 3. State Tracking
`ingestion_state` enables incremental API consumption and ensures efficient, repeatable ingestion runs.

### 4. Single Transaction Per Run
Using a single transaction:
- Ensures atomic ingestion
- Prevents partial updates
- Maintains consistency between dimensions and fact tables
- Aligns ingestion state with warehouse updates

---

## Future Improvements

- Soft delete handling
- Historical dimension tracking (SCD support)
- Partitioned fact table
- Materialized views
- Airflow / Prefect orchestration
- Data quality validation layer
- Performance monitoring metrics

---

## Purpose

This project was built to demonstrate:

- Incremental data pipeline design
- Warehouse modeling principles
- Hybrid snapshot strategies
- Transactional ingestion patterns
- Analytical view design
- End-to-end system thinking

It is intended as a portfolio-level demonstration of data engineering maturity rather than a simple API data collector.
