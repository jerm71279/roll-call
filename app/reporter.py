from __future__ import annotations
import csv
import io
from .models import StudentRecord, AssignmentResult


def build_report(
    students: list[StudentRecord],
    results: list[AssignmentResult],
    teacher_names: dict[int, list[str]],  # grade -> [teacher names in classroom order]
) -> dict:
    """
    Returns a dict with all view data needed by the Jinja2 templates.
    teacher_names maps grade -> list of teacher name strings (index = classroom index).
    """
    # index students by id
    student_map = {s.id: s for s in students}

    # build flat assignment rows: one dict per student
    rows = []
    for result in results:
        grade_teachers = teacher_names.get(result.grade, [])
        for student_id, classroom_idx in result.assignments.items():
            s = student_map.get(student_id)
            if not s:
                continue
            teacher = grade_teachers[classroom_idx] if classroom_idx < len(grade_teachers) else f"Class {classroom_idx + 1}"
            rows.append({
                "grade": result.grade,
                "classroom": classroom_idx + 1,
                "teacher": teacher,
                "last_name": s.last_name,
                "first_name": s.first_name,
                "gender": s.gender,
                "race": s.race,
                "iep": s.iep,
                "gifted": s.gifted,
                "ell": s.ell,
                "speech_only": s.speech_only,
                "ab_average": s.ab_average,
                "cd_average": s.cd_average,
                "f_average": s.f_average,
                "star_reading": s.star_reading,
                "iready_math": s.iready_math,
                "kinder_high": s.kinder_high,
                "kinder_medium": s.kinder_medium,
                "kinder_low": s.kinder_low,
                "student_id": student_id,
            })

    # grade summary: per grade → per classroom stats
    summary = []
    for result in results:
        grade_rows = [r for r in rows if r["grade"] == result.grade]
        grade_teachers = teacher_names.get(result.grade, [])
        classroom_stats = []
        n_classrooms = result.assignments and max(result.assignments.values()) + 1 or 0
        for c_idx in range(n_classrooms):
            c_rows = [r for r in grade_rows if r["classroom"] == c_idx + 1]
            teacher = grade_teachers[c_idx] if c_idx < len(grade_teachers) else f"Class {c_idx + 1}"
            classroom_stats.append({
                "teacher": teacher,
                "total": len(c_rows),
                "iep": sum(1 for r in c_rows if r["iep"]),
                "gifted": sum(1 for r in c_rows if r["gifted"]),
                "ell": sum(1 for r in c_rows if r["ell"]),
                "speech_only": sum(1 for r in c_rows if r["speech_only"]),
                "female": sum(1 for r in c_rows if r["gender"].upper() in ("F", "FEMALE")),
                "avg_ab": round(sum(r["ab_average"] for r in c_rows) / len(c_rows), 1) if c_rows else 0,
            })
        summary.append({
            "grade": result.grade,
            "grade_label": "Kinder" if result.grade == 0 else f"Grade {result.grade}",
            "solver_status": result.solver_status,
            "solve_time": result.solve_time_seconds,
            "classrooms": classroom_stats,
        })

    metrics = build_metrics(rows, results, teacher_names)

    return {
        "rows": rows,
        "summary": summary,
        "metrics": metrics,
    }


def build_metrics(
    rows: list[dict],
    results: list[AssignmentResult],
    teacher_names: dict[int, list[str]],
) -> list[dict]:
    """Per-grade, per-classroom breakdown data for dashboard charts."""
    grades_out = []
    for result in results:
        grade = result.grade
        is_kinder = grade == 0
        grade_rows = [r for r in rows if r["grade"] == grade]
        grade_teachers = teacher_names.get(grade, [])
        n_classrooms = max(result.assignments.values()) + 1 if result.assignments else 0

        classrooms_out = []
        for c_idx in range(n_classrooms):
            c_rows = [r for r in grade_rows if r["classroom"] == c_idx + 1]
            teacher = grade_teachers[c_idx] if c_idx < len(grade_teachers) else f"Class {c_idx + 1}"
            n = len(c_rows)

            gender = {
                "Male": sum(1 for r in c_rows if r["gender"].upper() in ("M", "MALE")),
                "Female": sum(1 for r in c_rows if r["gender"].upper() in ("F", "FEMALE")),
                "Other": sum(1 for r in c_rows if r["gender"].upper() not in ("M", "MALE", "F", "FEMALE")),
            }

            race_counts: dict[str, int] = {}
            for r in c_rows:
                race_counts[r["race"]] = race_counts.get(r["race"], 0) + 1

            flags = {
                "IEP": sum(1 for r in c_rows if r["iep"]),
                "Gifted": sum(1 for r in c_rows if r["gifted"]),
                "ELL": sum(1 for r in c_rows if r["ell"]),
                "Speech Only": sum(1 for r in c_rows if r["speech_only"]),
                "No Flag": sum(1 for r in c_rows if not any([r["iep"], r["gifted"], r["ell"], r["speech_only"]])),
            }

            if is_kinder:
                academic = {
                    "High": sum(1 for r in c_rows if r["kinder_high"]),
                    "Medium": sum(1 for r in c_rows if r["kinder_medium"]),
                    "Low": sum(1 for r in c_rows if r["kinder_low"]),
                }
            else:
                avg_ab  = round(sum(r["ab_average"] for r in c_rows) / n, 1) if n else 0
                avg_cd  = round(sum(r["cd_average"] for r in c_rows) / n, 1) if n else 0
                avg_f   = round(sum(r["f_average"] for r in c_rows) / n, 1) if n else 0
                avg_star = round(sum(r["star_reading"] for r in c_rows) / n, 2) if n else 0
                avg_math = round(sum(r["iready_math"] for r in c_rows) / n, 2) if n else 0
                academic = {"A-B%": avg_ab, "C-D%": avg_cd, "F%": avg_f,
                            "STAR Rdg": avg_star, "iReady Math": avg_math}

            classrooms_out.append({
                "teacher": teacher,
                "total": n,
                "gender": gender,
                "race": race_counts,
                "flags": flags,
                "academic": academic,
                "is_kinder": is_kinder,
            })

        grades_out.append({
            "grade": grade,
            "grade_label": "Kinder" if grade == 0 else f"Grade {grade}",
            "is_kinder": is_kinder,
            "classrooms": classrooms_out,
        })
    return grades_out


def reassign_student(
    report: dict,
    student_id: str,
    new_classroom: int,  # 1-based
) -> dict:
    """Apply a manual override — update the student's classroom in place."""
    for row in report["rows"]:
        if row["student_id"] == student_id:
            row["classroom"] = new_classroom
            break
    return report


def export_csv(report: dict) -> bytes:
    """Return CSV bytes of the full assignment report."""
    if not report["rows"]:
        return b""
    fieldnames = [
        "grade", "classroom", "teacher", "last_name", "first_name",
        "gender", "race", "iep", "gifted", "ell", "speech_only",
        "ab_average", "cd_average", "f_average", "star_reading", "iready_math",
        "kinder_high", "kinder_medium", "kinder_low",
    ]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(sorted(report["rows"], key=lambda r: (r["grade"], r["classroom"], r["last_name"])))
    return buf.getvalue().encode("utf-8")
