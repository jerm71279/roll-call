# Roll-Call — Internal Context

---

## Project Identity

| Field | Value |
|-------|-------|
| Project | Roll-Call — Roster Optimizer |
| Owner | Personal project |
| District | Baldwin County School system |
| School | Jubilee Elementary |
| Status | Scaffold complete — Sprint 1 pending |
| Started | 2026-06-12 |

---

## Intent & Strategic Goal

> **Intent:** Eliminate the 20-hour annual rostering burden for school administrators.
> **Goal:** ≤3 hours end-to-end — upload, optimize, review, export.

---

## Why This Exists

School administrators at Jubilee Elementary manually balance student rosters across classrooms each year. This takes ~20 hours and produces results that are difficult to defend when challenged by parents or staff. The tool makes the process fast, data-driven, and auditable.

---

## What Has Been Built

- CRISP-E interview complete (2026-06-12)
- Project scaffold generated
- AKS notebook registered (`e256bc96-8631-4528-8977-ae4f388de3ca`)
- Sample schema captured from `Class Rolls - School Roster.csv`

---

## What Is In Progress

- Sprint 1: Core optimizer (ingest → CP-SAT → CSV download)
- Sprint 2: Full UI + Render deploy

---

## Known Issues / Blockers

- Race column legal sensitivity — treat as view-only, not optimization target
- Render free tier 30s request timeout — solver timeout must stay below this
- Kinder grade requires separate High/Medium/Low tier logic vs. academic averages for grades 1–6

---

## Key Decisions Made

- FastAPI + Jinja2 + HTMX + Alpine.js (no React build step)
- OR-Tools CP-SAT for optimization
- Stateless — no database, no auth
- Two-CSV input: teacher roster sets classroom count, student roster drives placement
- Admin-configurable objective weights (IEP first, then academic, then gender)

---

## Useful Commands

```bash
# Dev server
uvicorn app.main:app --reload

# Tests
pytest tests/

# Lint
ruff check app/
```
