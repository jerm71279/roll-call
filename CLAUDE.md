# Roll-Call — Roster Optimizer

## Overview
AI-assisted equity optimization engine for K-12 school administrators. Accepts teacher and student roster CSVs, balances students across classrooms using CP-SAT constraint programming, and returns downloadable assignments with multiple demographic views.

**Owner:** Personal project — Baldwin County School system (Jubilee Elementary)
**Deployment:** Render (stateless web app)
**Repo:** jerm71279/roll-call

---

## Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.12 |
| Framework | FastAPI + Jinja2 + HTMX + Alpine.js |
| Optimizer | OR-Tools CP-SAT |
| Database | None (stateless) |
| Deploy | Render |

---

## Contents

```
roll-call/
├── app/
│   ├── main.py           # FastAPI app, routes
│   ├── ingest.py         # CSV parsing + validation
│   ├── optimizer.py      # CP-SAT solver (per-grade)
│   ├── reporter.py       # View formatting + CSV export
│   └── models.py         # Pydantic schemas
├── templates/            # Jinja2 HTML templates
├── static/               # CSS, JS (Alpine.js, HTMX)
├── tests/
├── render.yaml
├── pyproject.toml
└── CLAUDE.md
```

---

## Quick Start

```bash
pip install -e ".[dev]"
uvicorn app.main:app --reload
# Open http://localhost:8000
```

---

## Environment Variables

```
APP_ENV=dev
MAX_UPLOAD_MB=10
SOLVER_TIMEOUT_SECONDS=60
LOCK_MANUAL_EDITS=false
```

---

## Architecture Notes

- **Stateless:** No database, no auth. Upload → optimize → download → done.
- **Grades K–6:** Each grade processed independently. Can run all at once or one grade at a time.
- **Two-CSV input:** Teacher roster sets classroom count per grade; student roster drives placement.
- **Race column:** Used for visibility/reporting only — not an optimization target (FERPA + legal).
- **Manual override:** After optimization, admin can reassign individual students before export.
- **Solver timeout:** CP-SAT runs per grade with `SOLVER_TIMEOUT_SECONDS` limit; returns best solution found.
- **Objective weights:** Admin can set priority ranking (IEP balance > academic spread > gender) before running.

---

## Pipeline Stages

| Stage | File | Responsibility |
|-------|------|----------------|
| Ingest | `app/ingest.py` | Parse + validate both CSVs, match students to grades/teachers |
| Optimizer | `app/optimizer.py` | Run CP-SAT per grade, minimize weighted variance |
| Reporter | `app/reporter.py` | Format table views, generate CSV exports |

---

## Current Milestones

**Done:**
- CRISP-E interview complete
- Scaffold generated
- AKS notebook registered

**Next:**
- Sprint 1: Core optimizer working locally (upload → optimize → download CSV)
- Sprint 2: Full UI (multi-view tables, manual override, demographic export) deployed on Render
