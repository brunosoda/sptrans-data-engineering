# SPTrans Bus Data Engineering Pipeline

## Project Overview

This project builds a data engineering pipeline around São Paulo's SPTrans Olho Vivo API, initially focusing on bus line **516N-10**. The goal is to collect raw vehicle-position snapshots, store an auditable history, transform the data with dbt, and prepare reliable datasets for analysis.

The project is being developed incrementally. The current work focuses on API exploration and validating how to retrieve the line's vehicle positions. Database loading, dbt models, external data enrichment, CI/CD, and analytics are planned roadmap stages—not yet completed features.

## Goals

- Ingest real-time vehicle-position data from the SPTrans Olho Vivo API.
- Preserve raw API responses and collection timestamps.
- Build a historical dataset from repeated snapshots collected over time.
- Load raw data into PostgreSQL.
- Transform and test analytical models with dbt.
- Enrich bus-position data with external weather and traffic data where suitable sources are available.
- Use automated CI/CD checks to prevent failing dbt changes from reaching production.
- Make the resulting data useful for reproducible analysis and a future dashboard.

## Current Status

**In progress — API exploration and data discovery**

- Identified the API gateway and authenticated requests using an API Lib access token.
- Queried the line search endpoint for `516N-10`.
- Identified two internal line codes associated with the search results: `266` and `33034`.
- Successfully retrieved the general vehicle-position response and filtered it for those line codes.
- Inspected the nested JSON structure, including line-level metadata and vehicle-level position fields.

The initial successful test returned vehicle positions for both internal line codes. Vehicle counts vary by collection time and should not be treated as fixed.

> The project does not yet have a long-term historical dataset. Historical analysis will become possible as snapshots are collected and retained over time.

## Planned Architecture

```text
SPTrans Olho Vivo API
        |
        v
Python ingestion
  - HTTP requests
  - response validation
  - error handling and logs
        |
        v
Raw JSON snapshots
        |
        v
PostgreSQL raw layer
        |
        v
dbt transformations and tests
  - staging
  - intermediate
  - marts
        |
        +--------------------+
        |                    |
        v                    v
Weather data            Traffic data
(future integration)    (future integration)
        |                    |
        +----------+---------+
                   |
                   v
          Analytical datasets
                   |
                   v
       Dashboard and analysis
          (planned: Streamlit)
```

## Technology Stack

| Technology | Purpose | Status |
|---|---|---|
| Python | API requests and ingestion | In use for exploration |
| `requests` | HTTP requests | In use |
| `python-dotenv` | Load local environment variables | In use |
| SPTrans Olho Vivo API | Bus line and vehicle-position data | In use |
| JSON | Raw snapshot format | Planned |
| PostgreSQL | Raw storage and analytical database | Planned for this project |
| dbt Core | SQL transformations, tests, and documentation | Planned |
| GitHub Actions | CI/CD workflows | Planned |
| Streamlit | Potential analytical dashboard | Planned |
| Weather API | Weather enrichment | Under evaluation |
| Traffic API | Traffic enrichment | Under evaluation |

## Roadmap

### Phase 1 — API Exploration and Data Discovery

- [x] Test API authentication and connectivity.
- [x] Find the line `516N-10` and identify relevant internal line codes.
- [x] Inspect the JSON response hierarchy.
- [x] Retrieve and filter vehicle positions.
- [ ] Document the API response fields and their meanings.
- [ ] Review API terms, quotas, and collection constraints.

### Phase 2 — Python Ingestion Pipeline

- [ ] Replace exploratory scripts with a reusable ingestion module.
- [ ] Collect snapshots at a controlled, documented interval.
- [ ] Add request timeouts and explicit HTTP error handling.
- [ ] Validate expected JSON fields and data types.
- [ ] Log collection timestamps, outcomes, durations, and record counts.
- [ ] Save raw snapshots with collection metadata.
- [ ] Add tests for parsing and validation logic.
- [ ] Define a safe approach for token expiry and renewal.

### Phase 3 — PostgreSQL Raw Storage

- [ ] Create a dedicated local database and raw schema.
- [ ] Design tables for ingestion metadata and raw observations.
- [ ] Preserve collection timestamps and relevant source timestamps.
- [ ] Define a strategy for duplicate observations and repeatable loads.
- [ ] Validate row counts and basic data integrity.

### Phase 4 — dbt Transformations and Data Quality

- [ ] Configure the dbt project and PostgreSQL profile.
- [ ] Build staging models with consistent names and data types.
- [ ] Create intermediate models where business logic needs to be reused.
- [ ] Create marts for analysis.
- [ ] Add appropriate generic and singular tests.
- [ ] Document sources, models, columns, and lineage.
- [ ] Generate dbt documentation.

### Phase 5 — External Data Enrichment

- [ ] Evaluate weather data sources, coverage, licensing, and historical availability.
- [ ] Evaluate traffic data sources, coverage, licensing, and historical availability.
- [ ] Define how external observations will be matched by time and geographic proximity.
- [ ] Ingest and validate selected sources.
- [ ] Build dbt models that combine bus positions with relevant weather or traffic indicators.

External enrichment depends on finding suitable APIs and verifying their access conditions. Any relationship between traffic, weather, and bus movement will be treated as an analytical question, not assumed to be causal.

### Phase 6 — CI/CD with GitHub Actions

**Continuous Integration (CI), on every pull request**

- [ ] Install project dependencies and validate the dbt project.
- [ ] Build dbt models in an isolated temporary schema.
- [ ] Run applicable models, seeds, and tests with `dbt build`.
- [ ] Publish the check result to the pull request.
- [ ] Require successful checks before merging.
- [ ] Clean up the temporary schema, including after failures where possible.

**Continuous Deployment (CD), on merge to `main`**

- [ ] Run `dbt build` against the configured production target.
- [ ] Store the deployed `manifest.json` as an artifact for future state-based comparisons.
- [ ] Generate dbt documentation with `dbt docs generate`.
- [ ] Publish documentation and retain relevant run artifacts.
- [ ] Record deployment outcomes.

CI must not write to production tables. Production credentials and deployment permissions should be separate from those used by pull-request validation. Temporary schemas should be isolated per run to avoid collisions between concurrent pull requests.

### Phase 7 — Analytics and Monitoring

- [ ] Explore data coverage, observation frequency, and missing positions.
- [ ] Analyze vehicle positions over time and space.
- [ ] Investigate relationships with weather and traffic conditions when enriched data is available.
- [ ] Build a dashboard, potentially with Streamlit.
- [ ] Monitor ingestion failures, data freshness, and dbt test results.

## Data Quality and Reliability Principles

The pipeline will be designed around these principles:

- **Raw data preservation:** retain source responses so transformations can be reviewed and reprocessed.
- **Traceability:** record when each request and snapshot was collected.
- **Validation:** check response structure and expected fields before loading data.
- **Failure visibility:** log errors and failed requests without exposing credentials.
- **Reproducibility:** version code and dbt models in Git.
- **Safe deployments:** test model changes outside production before merging.
- **Honest reporting:** distinguish implemented features from planned work.

## Local Setup

### Requirements

- Python 3
- `pip`
- Access to the SPTrans Olho Vivo API through the configured API gateway
- A valid access token

### 1. Clone the repository

```bash
git clone <repository-url>
cd sptrans-project
```

### 2. Create and activate a virtual environment

On Ubuntu/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a local `.env` file. **Never commit this file or share its contents.**

```dotenv
SPTRANS_ACCESS_TOKEN=replace_with_your_access_token
SPTRANS_TOKEN=replace_with_legacy_token_if_needed
```

Only configure the variables needed by the script you are running. The legacy-token test uses `SPTRANS_TOKEN`; the API Lib gateway scripts use `SPTRANS_ACCESS_TOKEN`.

### 5. Run the exploratory scripts

```bash
python test_access_token.py
python test_positions.py
```

`test_api.py` tests the legacy SPTrans authentication endpoint and is retained as an exploratory script. The currently working gateway flow uses the API Lib access token.

The position test requests the general `/Posicao` response and filters it for the internal codes identified for line `516N-10`. It currently retrieves the wider position response before filtering locally.

## Security

- Keep `.env` out of Git.
- Do not hard-code access tokens, API keys, passwords, or other secrets.
- Do not print tokens in logs or error messages.
- Use `.env.example` only for variable names and placeholder values.
- Review files and Git status before the first commit and before pushing.
- If a credential is exposed, revoke or replace it where possible; adding it to `.gitignore` does not remove it from Git history.

## Limitations

- Historical data begins only when collection starts; the API query does not automatically provide the project's own historical snapshots.
- Vehicle counts and positions change over time.
- Automatic token renewal is not implemented yet.
- PostgreSQL loading, dbt models, external enrichment, CI/CD, and the dashboard are planned, not completed.
- Weather and traffic integration depends on the availability and terms of suitable data sources.

## License and Data Source

This project uses the SPTrans Olho Vivo API. Before distributing collected data or publishing derived datasets, review the API's applicable terms, usage limits, and attribution requirements.

The project code's license has not yet been selected.
