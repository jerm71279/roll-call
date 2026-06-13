from __future__ import annotations
import json
import os
import uuid
from pathlib import Path

from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .ingest import build_grade_packets, parse_teacher_roster
from .models import ObjectiveWeights
from .optimizer import optimize_grade
from .reporter import build_report, reassign_student, export_csv

_MAX_MB = int(os.environ.get("MAX_UPLOAD_MB", "10"))
_LOCK_EDITS = os.environ.get("LOCK_MANUAL_EDITS", "false").lower() == "true"

BASE_DIR = Path(__file__).parent.parent
app = FastAPI(title="Roll-Call — Roster Optimizer")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# In-memory store: run_id -> {report, teacher_names}
_runs: dict[str, dict] = {}


@app.get("/", response_class=HTMLResponse)
async def upload_form(request: Request):
    return templates.TemplateResponse(request, "upload.html")


@app.post("/upload", response_class=HTMLResponse)
async def handle_upload(
    request: Request,
    teacher_csv: UploadFile = File(...),
    student_csv: UploadFile = File(...),
    weight_iep: float = Form(3.0),
    weight_academic: float = Form(2.0),
    weight_gender: float = Form(1.0),
    weight_gifted: float = Form(1.0),
    weight_ell: float = Form(1.0),
    weight_speech: float = Form(1.0),
    grades: str = Form("all"),  # "all" or comma-separated grade numbers
):
    teacher_raw = await teacher_csv.read()
    student_raw = await student_csv.read()

    if len(teacher_raw) > _MAX_MB * 1024 * 1024 or len(student_raw) > _MAX_MB * 1024 * 1024:
        raise HTTPException(400, f"File exceeds {_MAX_MB}MB limit")

    weights = ObjectiveWeights(
        iep=weight_iep,
        academic=weight_academic,
        gender=weight_gender,
        gifted=weight_gifted,
        ell=weight_ell,
        speech_only=weight_speech,
    )

    grade_list = None if grades.strip() == "all" else [int(g) for g in grades.split(",")]

    try:
        packets = build_grade_packets(teacher_raw, student_raw, weights, grade_list)
    except ValueError as e:
        return templates.TemplateResponse(request, "upload.html", {"error": str(e)})

    # Divide solver budget evenly across grades so all-grades runs stay inside
    # Render's 30s HTTP timeout (SOLVER_TIMEOUT_SECONDS defaults to 25 in prod).
    _SOLVER_TIMEOUT = int(os.environ.get("SOLVER_TIMEOUT_SECONDS", "60"))
    per_grade_timeout = max(3, _SOLVER_TIMEOUT // max(len(packets), 1))
    results = [optimize_grade(p, timeout=per_grade_timeout) for p in packets]

    # build teacher_names map from teacher roster
    import csv as csv_mod, io
    teacher_names: dict[int, list[str]] = {}
    reader = csv_mod.DictReader(io.StringIO(teacher_raw.decode("utf-8-sig")))
    for row in reader:
        grade = int(row["Grade"].strip())
        teacher_names.setdefault(grade, []).append(row["Teacher Name"].strip())

    all_students = [s for p in packets for s in p.students]
    report = build_report(all_students, results, teacher_names)

    run_id = str(uuid.uuid4())
    _runs[run_id] = {"report": report, "teacher_names": teacher_names}

    return templates.TemplateResponse(request, "results.html", {
        "run_id": run_id,
        "report": report,
        "lock_edits": _LOCK_EDITS,
    })


@app.get("/results/{run_id}", response_class=HTMLResponse)
async def view_results(request: Request, run_id: str, view: str = "summary"):
    run = _runs.get(run_id)
    if not run:
        raise HTTPException(404, "Run not found — results are not persisted across server restarts")
    return templates.TemplateResponse(request, "results.html", {
        "run_id": run_id,
        "report": run["report"],
        "view": view,
        "lock_edits": _LOCK_EDITS,
    })


@app.get("/results/{run_id}/dashboard", response_class=HTMLResponse)
async def view_dashboard(request: Request, run_id: str):
    run = _runs.get(run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    return templates.TemplateResponse(request, "dashboard.html", {
        "run_id": run_id,
        "metrics_json": json.dumps(run["report"]["metrics"]),
    })


@app.get("/results/{run_id}/export")
async def export_run(run_id: str):
    run = _runs.get(run_id)
    if not run:
        raise HTTPException(404, "Run not found")
    csv_bytes = export_csv(run["report"])
    return StreamingResponse(
        iter([csv_bytes]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=roster-balanced-{run_id[:8]}.csv"},
    )


@app.post("/results/{run_id}/reassign")
async def manual_reassign(request: Request, run_id: str):
    if _LOCK_EDITS:
        raise HTTPException(403, "Manual edits are disabled")
    run = _runs.get(run_id)
    if not run:
        raise HTTPException(404, "Run not found")

    body = await request.json()
    student_id = body.get("student_id")
    new_classroom = int(body.get("classroom", 0))
    if not student_id or not new_classroom:
        raise HTTPException(400, "student_id and classroom required")

    run["report"] = reassign_student(run["report"], student_id, new_classroom)
    return {"status": "ok"}
