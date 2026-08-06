# GitHub Repository Analytics Platform

An end-to-end data engineering platform that incrementally ingests GitHub repository data, maintains a historical analytical warehouse, and archives long-term data to Amazon S3 using Apache Parquet.

The platform demonstrates modern data engineering practices including incremental ingestion, dimensional modeling, historization, cloud data warehousing, cold storage, and automated batch orchestration.

> **Built to learn end-to-end data engineering by designing a complete data platform.**

---

## Highlights

* Incremental GitHub API ingestion with state tracking
* Daily historical snapshots using a hybrid historization strategy
* Dimensional data warehouse built on PostgreSQL
* Two-phase ingestion pipeline optimized for managed cloud databases
* Automated daily execution with GitHub Actions
* Historical data archival to Amazon S3 using Apache Parquet
* SQL analytical views for reporting and trend analysis
* Modular Python codebase with pytest-based testing
* Production-inspired architecture emphasizing maintainability and scalability

---

## Overview

The GitHub Repository Analytics Platform is an end-to-end batch data engineering project that collects, models, and analyzes repository metadata from GitHub.

The project was built to explore the complete lifecycle of a modern data platform—from data ingestion and warehouse design to historical tracking, analytics, and data lifecycle management. Rather than focusing solely on ETL, it demonstrates how different components of a data engineering system work together to transform operational API data into an analytical data warehouse.

Repository metadata is collected incrementally using the GitHub REST API and stored in a PostgreSQL warehouse using a dimensional data model. Historical repository and language metrics are preserved through a hybrid historization strategy that combines event-driven ingestion with daily snapshot generation, ensuring a continuous time series while minimizing unnecessary API requests.

As historical data grows, older snapshots are archived to Amazon S3 in Apache Parquet format, allowing the operational warehouse to remain compact while preserving long-term analytical history.

The project evolved iteratively as new engineering challenges emerged, introducing language analytics, cloud database deployment, a two-phase ingestion pipeline to address managed database connection constraints, warehouse retention policies, and a dedicated cold storage layer.

The result is a modular, production-inspired data platform that emphasizes maintainability, analytical correctness, and practical data engineering design principles.

---

## Why This Project?

Many portfolio projects demonstrate how to build an ETL pipeline. This project focuses on the broader challenges involved in designing a complete data platform.

It explores concepts such as:

* Incremental API ingestion
* Dimensional warehouse modeling
* Historical snapshot management
* Time-series analytics
* Data lifecycle management
* Batch pipeline orchestration
* Cloud-hosted data warehousing
* Modular software architecture

By addressing these challenges in a single project, the platform demonstrates not only implementation skills but also the architectural decisions required to build maintainable analytical systems.

---

## Architecture

The platform follows a modular batch-processing architecture that separates data ingestion, warehouse management, analytics, and archival into independent components.

```text
                           +----------------------+
                           |    GitHub REST API   |
                           +----------+-----------+
                                      |
                                      | Incremental Fetch
                                      |
                           +----------v-----------+
                           |  Ingestion Pipeline  |
                           |      (Python)        |
                           +----------+-----------+
                                      |
                         Transform & Validate Data
                                      |
                           +----------v-----------+
                           | PostgreSQL Warehouse |
                           +----------+-----------+
                                      |
             +------------------------+------------------------+
             |                                                 |
             |                                                 |
+------------v------------+                    +---------------v--------------+
|   Analytical SQL Views  |                    |  Cold Storage Archival       |
|                         |                    | (Parquet → Amazon S3)        |
+------------+------------+                    +---------------+--------------+
             |                                                 |
             |                                                 |
     Dashboards / Reports                           Long-Term Historical Data
```

### Architectural Principles

The platform was designed around a few key engineering principles:

* **Incremental Ingestion** — Only repositories updated since the previous successful run are fetched from GitHub.
* **Historical First** — The warehouse maintains a complete daily history of repository metrics rather than only the latest state.
* **Separation of Concerns** — API communication, orchestration, database operations, and archival are implemented as independent modules.
* **Operational Efficiency** — A two-phase ingestion pipeline minimizes long-lived database connections and accommodates managed cloud database constraints.
* **Data Lifecycle Management** — Recent analytical data remains in PostgreSQL while older snapshots are archived to Amazon S3 in Apache Parquet format.

Together, these principles allow the platform to balance efficient data collection, analytical completeness, maintainability, and long-term scalability.

---

## Key Features

### Incremental GitHub API Ingestion

The platform performs incremental data ingestion by tracking the timestamp of the last successful execution for each organization. Only repositories updated since the previous run are requested from the GitHub REST API, reducing unnecessary API calls and improving pipeline efficiency.

---

### Hybrid Historization Strategy

The warehouse combines **event-driven ingestion** with **time-driven historization**.

* Updated repositories receive fresh data from GitHub.
* Unchanged repositories inherit the previous day's state.

This guarantees a complete daily history for every tracked repository while minimizing API usage.

---

### Dimensional Data Warehouse

Repository data is organized using a dimensional model consisting of:

* Dimension tables for descriptive entities
* Fact tables for historical repository metrics
* Separate fact tables for programming language analytics

This structure supports efficient analytical queries while preserving historical data.

---

### Two-Phase Ingestion Pipeline

The ingestion workflow is divided into separate read and write phases.

By avoiding long-lived database connections during API calls, the pipeline remains compatible with managed cloud databases such as Neon, which suspend idle connections.

---

### Historical Analytics

Rather than storing only the latest repository state, the platform records daily snapshots that enable:

* Repository growth analysis
* Historical trend reporting
* Language evolution
* Organization-level analytics
* Time-series SQL queries

---

### Cold Storage Lifecycle

To control warehouse growth, historical snapshots older than the configured retention period are automatically archived to Amazon S3 as Apache Parquet files.

This keeps the operational warehouse lightweight while preserving complete historical data.

---

### SQL Analytics Layer

The warehouse exposes analytical SQL views for common reporting scenarios, including:

* Daily repository growth
* Organization statistics
* Language popularity
* Repository rankings
* Activity scoring

These views provide a foundation for dashboards and downstream analytical applications.

---

### Modular Architecture

The project separates ingestion, API communication, database access, configuration, testing, and archival into independent modules.

This improves maintainability, simplifies testing, and allows new features to be introduced with minimal impact on existing components.

---

### Cloud-Native Deployment

The platform runs as a scheduled GitHub Actions workflow with a cloud-hosted PostgreSQL warehouse, demonstrating a complete automated batch data pipeline from ingestion through archival.

---

## Technology Stack

| Category                 | Technologies                       | Purpose                                                                             |
| ------------------------ | ---------------------------------- | ----------------------------------------------------------------------------------- |
| **Programming Language** | Python                             | Core application logic, data ingestion, transformation, orchestration, and archival |
| **Data Source**          | GitHub REST API                    | Incremental retrieval of repository metadata and language statistics                |
| **Data Warehouse**       | PostgreSQL (Neon)                  | Stores dimensional data and historical analytical snapshots                         |
| **Data Modeling**        | Star Schema / Dimensional Modeling | Organizes entities and historical measurements for analytical workloads             |
| **Cold Storage**         | Amazon S3, Apache Parquet, PyArrow | Archives historical snapshots in a compressed columnar format                       |
| **Automation**           | GitHub Actions                     | Executes the ingestion pipeline on a daily schedule                                 |
| **Database Access**      | psycopg2                           | PostgreSQL connectivity and high-performance bulk loading                           |
| **Testing**              | pytest, unittest.mock              | Unit testing using mocked external dependencies                                     |
| **Development**          | Git, GitHub, Makefile              | Version control and local development workflow                                      |

---

## Why These Technologies?

### PostgreSQL (Neon)

PostgreSQL offers a mature relational database with strong SQL capabilities, making it an excellent choice for dimensional modeling and analytical workloads. Deploying on Neon also introduced practical cloud database considerations such as connection lifecycle management.

### Amazon S3 & Apache Parquet

As historical data grows, storing every snapshot in the operational warehouse becomes inefficient. Amazon S3 combined with Apache Parquet provides a cost-effective archival layer that preserves historical data while keeping the warehouse lightweight.

### GitHub Actions

GitHub Actions automates daily pipeline execution without requiring additional infrastructure, allowing the project to function as a scheduled batch processing system.

---

## Project Structure

```text
.
├── .github/
│   └── workflows/          # GitHub Actions workflow for scheduled ingestion
│
├── sql/
│   ├── schema.sql          # Warehouse schema definition
│   └── views.sql           # Analytical SQL views
│
├── src/
│   ├── ingest.py           # Pipeline orchestration
│   ├── github_client.py    # GitHub API client
│   ├── db.py               # Database operations
│   ├── archive.py          # Cold storage archival
│   ├── config.py           # Configuration management
│   └── ...
│
├── tests/                  # Pytest test suite
│
├── docs/                   # Technical documentation
│
├── requirements.txt
├── Makefile
└── README.md
```

### Directory Overview

| Directory              | Purpose                                                                                                                                         |
| ---------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| **src/**               | Contains the application's core business logic, including data ingestion, API communication, warehouse operations, configuration, and archival. |
| **sql/**               | Defines the warehouse schema and analytical SQL views used for reporting and trend analysis.                                                    |
| **tests/**             | Contains pytest-based unit tests for validating core business logic and database operations.                                                    |
| **.github/workflows/** | Automates daily execution of the ingestion pipeline using GitHub Actions.                                                                       |
| **docs/**              | Contains detailed technical documentation covering architecture, data modeling, ingestion strategy, testing, and design decisions.              |

### Core Components

| Component              | Responsibility                                                                            |
| ---------------------- | ----------------------------------------------------------------------------------------- |
| **GitHub Client**      | Fetches repository metadata and language statistics from the GitHub REST API.             |
| **Ingestion Pipeline** | Coordinates incremental ingestion, transformation, historization, and warehouse loading.  |
| **Database Layer**     | Encapsulates all PostgreSQL interactions and bulk data operations.                        |
| **Archive Layer**      | Moves historical snapshots from PostgreSQL to Amazon S3 as Apache Parquet files.          |
| **Analytics Layer**    | Provides SQL views for reporting, trend analysis, and downstream analytical applications. |

---

## Roadmap

This project is an ongoing exploration of modern data engineering practices. Future enhancements include:

* [ ] Expand pytest coverage to include recently added components.
* [ ] Introduce workflow orchestration using Apache Airflow or Prefect.
* [ ] Add data quality validation and pipeline health monitoring.
* [ ] Build an interactive analytics dashboard powered by the warehouse.
* [ ] Improve observability with pipeline metrics and alerting.
* [ ] Support additional GitHub entities such as pull requests, releases, workflows, and contributors.
* [ ] Evaluate larger-scale analytical warehouses as data volume increases.

---

## About This Project

This repository was built as a personal learning project to explore the complete lifecycle of a modern data engineering platform.

The focus extends beyond building an ETL pipeline to understanding how data is ingested, modeled, historized, archived, and prepared for analytical consumption while making engineering decisions that reflect real-world data platform design.

As the project evolved, new architectural patterns and capabilities were introduced incrementally to address practical challenges encountered during development, making the repository a record of both technical implementation and engineering learning.
