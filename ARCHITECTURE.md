# Roll-Call — Architecture

## System Overview

Stateless FastAPI web app. Admin uploads two CSVs (teacher roster + student roster), selects grades and objective weights, and receives balanced classroom assignments as interactive tables and CSV downloads. No database, no authentication, no external services.

---

## Component Map

```
Browser (Admin)
    │
    │  POST /upload (multipart: teacher_csv, student_csv)
    ▼
FastAPI (app/main.py)
    │
    ├── Ingest (app/ingest.py)
    │       Parse CSVs → validate schema → build StudentRecord list
    │
    ├── Optimizer (app/optimizer.py)
    │       For each grade:
    │         CP-SAT solver → minimize weighted variance across
    │         IEP load, academic tiers, gender, service flags
    │         Returns: {student_id → classroom_id} assignment map
    │
    └── Reporter (app/reporter.py)
            Build view DataFrames (summary, by-demographic, per-class)
            Render Jinja2 tables + generate CSV bytes

Browser (Admin)
    ├── View: Summary table (all grades)
    ├── View: Per-grade breakdown
    ├── View: Demographic index (filter by gender/race/IEP/etc.)
    ├── Manual override: reassign students via HTMX swap
    └── Export: Download CSV
```

---

## Data Flow

```
teacher_roster.csv     student_roster.csv
       │                       │
       └──────── Ingest ───────┘
                     │
              GradePacket[]
              (students, teachers, weights)
                     │
               Optimizer (CP-SAT)
                     │
              AssignmentResult[]
              (student → classroom)
                     │
                Reporter
                     │
         ┌───────────┼───────────┐
     HTML tables   Views     CSV export
```

---

## Input Schema

### teacher_roster.csv
| Column | Type | Notes |
|--------|------|-------|
| Grade | int | 0=Kinder, 1–6 |
| Teacher Name | str | One row per classroom |

### student_roster.csv
| Column | Type | Notes |
|--------|------|-------|
| Last Name | str | |
| First Name | str | |
| Gender | str | M/F/Other |
| Race | str | Visibility/reporting only — not optimized |
| A-B Average | float | % of grades A or B |
| C-D Average | float | % of grades C or D |
| F Average | float | % of failing grades |
| STAR Reading Grade Equivalent | float | |
| i-Ready Math Grade Level | float | |
| High (Kinder only) | bool | |
| Medium (Kinder only) | bool | |
| Low (Kinder Only) | bool | |
| IEP | bool | Special education flag |
| Gifted | bool | |
| ELL | bool | English Language Learner |
| Speech Only | bool | Speech services only |

---

## Key Interfaces

| Interface | Type | Direction | Notes |
|-----------|------|-----------|-------|
| `/` | GET | → Browser | Upload form |
| `/upload` | POST | Browser → | Multipart CSV upload + weight config |
| `/results/{run_id}` | GET | → Browser | Table views (Jinja2) |
| `/results/{run_id}/export` | GET | → Browser | CSV download |
| `/results/{run_id}/reassign` | POST | Browser → | Manual override (HTMX) |

---

## Deployment Topology

```
Render Web Service
  └── Single instance
        ├── uvicorn app.main:app
        ├── In-memory result cache (dict, keyed by run_id UUID)
        └── No persistent storage
```

Run results are held in memory for the session. Render free tier spins down after inactivity — results do not persist across cold starts.

---

## Security Notes

- Student data (names, IEP status, race) is FERPA-protected PII for minors
- Data is processed in-memory only — never written to disk or logs
- Upload page displays a data-handling disclaimer
- No auth layer — access control by URL obscurity (run_id UUID)
- Never log request bodies containing CSV data

---

## Decision Log

| Decision | Choice | Rationale | Panel Flags |
|----------|--------|-----------|-------------|
| Optimizer | OR-Tools CP-SAT | Research-backed, handles multi-objective ILP cleanly | Solver timeout on large grades |
| Frontend | Jinja2 + HTMX + Alpine.js | No build step, adequate for stateless tool | React overkill for this scope |
| Persistence | None (stateless) | Simplest Render deploy, no DB cost | Results lost on cold start |
| Race column | View-only | Legal/ethical risk of race-as-optimization-target | Equity Counsel flag |
| Objective weights | Admin-configurable | Principals weight IEP load differently than gender balance | Equal weights produce wrong-feeling results |
