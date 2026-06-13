# Roll-Call — Roster Optimizer

> AI-assisted equity optimization engine for K-12 school administrators.

Upload your teacher and student rosters, set your priorities, and get balanced classroom assignments in seconds — not hours.

---

## What It Does

| Step | What happens |
|------|-------------|
| Upload | Teacher roster (sets classroom count) + student roster (K–6 attributes) |
| Configure | Set objective weights (IEP balance, academic spread, gender, service flags) |
| Optimize | CP-SAT solver balances students across classrooms per grade |
| Review | Multi-view tables — summary, per-grade, demographic index |
| Override | Manually reassign individual students before export |
| Export | Download balanced roster as CSV |

---

## Stack

- **Backend:** Python 3.12 / FastAPI / OR-Tools CP-SAT
- **Frontend:** Jinja2 + HTMX + Alpine.js
- **Deploy:** Render

---

## Quick Start

```bash
# Install
pip install -e ".[dev]"

# Run locally
uvicorn app.main:app --reload

# Open
open http://localhost:8000
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_ENV` | `dev` | dev / prod |
| `MAX_UPLOAD_MB` | `10` | CSV upload size cap |
| `SOLVER_TIMEOUT_SECONDS` | `60` | CP-SAT time limit per grade |
| `LOCK_MANUAL_EDITS` | `false` | Set true for read-only mode |

---

## Data Privacy

This application processes FERPA-protected student data. Data is held in memory only during your session and is never stored to disk, logged, or transmitted to third parties.
