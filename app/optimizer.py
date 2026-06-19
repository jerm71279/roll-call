from __future__ import annotations
import os
import time
from ortools.sat.python import cp_model
from .models import GradePacket, AssignmentResult

_TIMEOUT = int(os.environ.get("SOLVER_TIMEOUT_SECONDS", "60"))
_SCALE = 1000  # float → int scaling for CP-SAT


def _scaled(v: float) -> int:
    return int(round(v * _SCALE))


def _add_hard_balance(
    model: cp_model.CpModel,
    assignments: list[list[cp_model.IntVar]],
    vals: list[int],
    n_classes: int,
) -> None:
    """Guarantee floor/ceil distribution (max spread = 1) for a binary dimension."""
    n = len(vals)
    total = sum(vals)
    if total == 0 or total == n:
        return
    base, _ = divmod(total, n_classes)
    for c in range(n_classes):
        c_sum = sum(assignments[s][c] * vals[s] for s in range(n))
        model.Add(c_sum <= base + 1)
        model.Add(c_sum >= base)


def _add_variance_objective(
    model: cp_model.CpModel,
    assignments: list[list[cp_model.IntVar]],
    values: list[int],
    n_classes: int,
    weight: int,
) -> list[tuple]:
    """Add weighted variance term across classrooms for one dimension."""
    n_students = len(values)
    if n_students == 0 or weight == 0:
        return []

    total = sum(values)
    class_sums = []
    for c in range(n_classes):
        s = model.NewIntVar(0, total, f"sum_c{c}_dim")
        model.Add(s == sum(assignments[i][c] * values[i] for i in range(n_students)))
        class_sums.append(s)

    # minimize max - min (range) as variance proxy — simpler than true variance for CP-SAT
    max_sum = model.NewIntVar(0, total, "max_sum")
    min_sum = model.NewIntVar(0, total, "min_sum")
    model.AddMaxEquality(max_sum, class_sums)
    model.AddMinEquality(min_sum, class_sums)
    range_var = model.NewIntVar(0, total, "range")
    model.Add(range_var == max_sum - min_sum)
    return [(range_var, weight)]


def optimize_grade(packet: GradePacket, timeout: int = _TIMEOUT) -> AssignmentResult:
    students = packet.students
    n = len(students)
    k = packet.teacher_count
    w = packet.weights

    if n == 0:
        return AssignmentResult(grade=packet.grade, assignments={}, solver_status="OPTIMAL", solve_time_seconds=0.0)

    model = cp_model.CpModel()

    # x[s][c] = 1 if student s assigned to classroom c
    x = [[model.NewBoolVar(f"x_{s}_{c}") for c in range(k)] for s in range(n)]

    # each student assigned to exactly one classroom
    for s in range(n):
        model.AddExactlyOne(x[s])

    # class sizes: all classes get base or base+1 students (max spread = 1)
    base, _ = divmod(n, k)
    for c in range(k):
        model.Add(sum(x[s][c] for s in range(n)) <= base + 1)
        model.Add(sum(x[s][c] for s in range(n)) >= base)

    # hard balance constraints: floor/ceil for every dimension (guarantees max spread = 1)
    iep_vals    = [1 if s.iep else 0 for s in students]
    gifted_vals = [1 if s.gifted else 0 for s in students]
    ell_vals    = [1 if s.ell else 0 for s in students]
    speech_vals = [1 if s.speech_only else 0 for s in students]
    gender_vals = [1 if s.gender.upper() in ("F", "FEMALE") else 0 for s in students]

    for vals in [iep_vals, gifted_vals, ell_vals, speech_vals]:
        _add_hard_balance(model, x, vals, k)

    # race: hard balance per category so no group is concentrated in one class
    races = sorted(set(s.race for s in students))
    for race in races:
        race_vals = [1 if s.race == race else 0 for s in students]
        _add_hard_balance(model, x, race_vals, k)

    # soft objectives: minimize residual variance within the hard-constrained range
    is_kinder = packet.grade == 0
    objectives: list[tuple] = []

    if is_kinder:
        for vals, weight in [
            ([_scaled(1.0) if s.kinder_high else 0 for s in students], int(w.academic * _SCALE)),
            ([_scaled(1.0) if s.kinder_low else 0 for s in students], int(w.academic * _SCALE)),
        ]:
            objectives += _add_variance_objective(model, x, vals, k, weight)
    else:
        academic_vals = [_scaled(s.ab_average - s.f_average) for s in students]
        objectives += _add_variance_objective(model, x, academic_vals, k, int(w.academic * _SCALE))

    objectives += _add_variance_objective(model, x, iep_vals, k, int(w.iep * _SCALE))
    objectives += _add_variance_objective(model, x, gender_vals, k, int(w.gender * _SCALE))
    objectives += _add_variance_objective(model, x, gifted_vals, k, int(w.gifted * _SCALE))
    objectives += _add_variance_objective(model, x, ell_vals, k, int(w.ell * _SCALE))
    objectives += _add_variance_objective(model, x, speech_vals, k, int(w.speech_only * _SCALE))

    if objectives:
        weighted_sum = sum(var * wt for var, wt in objectives)
        model.Minimize(weighted_sum)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = timeout
    solver.parameters.num_search_workers = 4

    start = time.time()
    status = solver.Solve(model)
    elapsed = round(time.time() - start, 2)

    status_name = solver.StatusName(status)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return AssignmentResult(
            grade=packet.grade, assignments={},
            solver_status=status_name, solve_time_seconds=elapsed,
        )

    assignments = {}
    for s_idx, student in enumerate(students):
        for c in range(k):
            if solver.Value(x[s_idx][c]):
                assignments[student.id] = c
                break

    return AssignmentResult(
        grade=packet.grade,
        assignments=assignments,
        solver_status=status_name,
        solve_time_seconds=elapsed,
    )
