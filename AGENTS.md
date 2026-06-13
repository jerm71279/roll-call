# Roll-Call — Pipeline Stages

## Overview

Roll-call is a deterministic optimization pipeline, not a multi-agent system. Three named stages handle ingest, solving, and reporting.

---

## Stages

| # | Stage | File | Role | Failure Mode | Remediation |
|---|-------|------|------|--------------|-------------|
| 1 | Ingest | `app/ingest.py` | Parse + validate both CSVs, match students to grades/teachers | Malformed CSV, missing required columns, grade mismatch | Return field-level validation errors to the upload form |
| 2 | Optimizer | `app/optimizer.py` | Run CP-SAT solver per grade, minimize weighted variance | Solver timeout, infeasible constraints | Return best solution found within timeout; surface warning to admin |
| 3 | Reporter | `app/reporter.py` | Format results into table views, generate CSV exports | Empty result set, column mismatch | Show empty-state message; log stage and input shape |

---

## Stage Details

### Ingest
- Reads teacher_roster.csv: extracts grade → teacher list (determines classroom count per grade)
- Reads student_roster.csv: validates 16-column schema, infers grade going into
- Outputs: `List[GradePacket]` — one per grade, containing students + teacher slots + admin weights

### Optimizer
- Input: `GradePacket` (per grade)
- Runs CP-SAT with configurable `SOLVER_TIMEOUT_SECONDS`
- Objective: minimize weighted sum of per-classroom variance across IEP count, academic tier distribution, gender count, Gifted/ELL/Speech counts
- Kinder: uses High/Medium/Low tiers instead of academic averages
- Output: `AssignmentResult` — student_id → classroom_id mapping

### Reporter
- Input: `List[AssignmentResult]` + original student data
- Builds views: summary (all grades), per-grade detail, demographic index
- Generates downloadable CSV: student name + assigned classroom + all original columns
- Supports manual override: accepts reassignment POST, recalculates balance metrics live

---

## Orchestration

Sequential pipeline — Ingest → Optimizer → Reporter. Each stage runs synchronously per request. No message queue, no async workers. Render's 30s request timeout is the practical ceiling; `SOLVER_TIMEOUT_SECONDS` should be set below that.

---

## Status

| Stage | Status |
|-------|--------|
| Ingest | Not started |
| Optimizer | Not started |
| Reporter | Not started |
