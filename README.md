# DocAssistIQ

Evidence-grounded Clinical Decision Support platform for qualified healthcare professionals.

## Prerequisites

- Node.js >= 18
- Python >= 3.11
- PostgreSQL 15+ with pgvector (required in later phases)
- Redis (required in later phases)

## Quick Start

### Frontend

```bash
cd frontend
npm install
npm run dev
# Open http://localhost:3000
```

### Backend

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# API at http://localhost:8000
# Docs at http://localhost:8000/docs
```

### Environment

```bash
cp .env.example .env
# Fill in actual values in .env
```

## Project Structure

```
frontend/    — Next.js + React + TypeScript + TailwindCSS
backend/     — FastAPI + Pydantic + SQLAlchemy + Alembic
ml/          — Machine learning development
data/        — Datasets and data artifacts
tests/       — Root-level test orchestration
scripts/     — Developer scripts
infra/       — Infrastructure configuration
docs/        — Documentation
.github/     — GitHub Actions CI/CD
```

## Commands

| Task                    | Command                                  |
| ----------------------- | ---------------------------------------- |
| Frontend dev server     | `cd frontend && npm run dev`             |
| Frontend build          | `cd frontend && npm run build`           |
| Frontend lint           | `cd frontend && npm run lint`            |
| Frontend typecheck      | `cd frontend && npx tsc --noEmit`        |
| Frontend test           | `cd frontend && npm test`                |
| Backend dev server      | `cd backend && uvicorn app.main:app --reload` |
| Backend lint            | `cd backend && ruff check .`             |
| Backend format          | `cd backend && ruff format .`            |
| Backend typecheck       | `cd backend && mypy app/`                |
| Backend test            | `cd backend && pytest`                   |
