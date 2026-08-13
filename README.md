# Weather Tracking & Analysis Dashboard

Web application that ingests weather data from external providers, stores and analyses
time-series history, and presents current conditions, trends and alerts through an
interactive dashboard.

This repository is built from the project Work Breakdown Structure
(`Weather_Dashboard_WBS.xlsx`). Work is delivered incrementally: this **foundation** PR
lands the code base that every WBS task builds on, and each subsequent PR implements a
single WBS task.

## Architecture

| Layer     | Stack                                                              |
| --------- | ----------------------------------------------------------------- |
| Backend   | Python 3.11+, FastAPI, SQLAlchemy 2.x, Pydantic v2, pytest        |
| Frontend  | React 18, TypeScript, Vite                                        |
| Data      | SQLAlchemy ORM (SQLite for dev/CI; ready for a time-series store) |
| CI        | GitHub Actions (backend pytest + frontend build)                  |

```
backend/
  app/
    api/        # FastAPI routers
    core/       # config, database, shared plumbing
    models/     # SQLAlchemy ORM models
    schemas/    # Pydantic request/response models
    services/   # business logic (ingestion, analytics, providers)
    main.py     # app factory + wiring
  tests/        # pytest suite
frontend/
  src/          # React + TypeScript app
```

## WBS delivery map

| WBS   | Title                                    | Status                    |
| ----- | ---------------------------------------- | ------------------------- |
| —     | Project foundation & scaffolding         | this PR                   |
| 1.1.1 | [BE] Integrate external weather providers| follow-up PR              |
| 1.1.2 | [BE] Scheduled ingestion & polling jobs  | follow-up PR              |
| 1.1.3 | [BE] Normalise & store time-series data  | follow-up PR              |
| 1.1.4 | [BE] Rate limiting, retries & caching    | follow-up PR              |
| 1.2 … | Backend Core API & later requirements    | subsequent PRs            |

## Getting started

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
# API docs at http://localhost:8000/docs
```

Run the tests:

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# app at http://localhost:5173
```

## Configuration

Backend settings are read from environment variables (see `backend/.env.example`).
Copy it to `backend/.env` and adjust as needed.
