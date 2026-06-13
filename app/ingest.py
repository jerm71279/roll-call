from __future__ import annotations
import csv
import io
import uuid
from .models import StudentRecord, GradePacket, ObjectiveWeights

_STUDENT_COLUMNS = {
    "Last Name", "First Name", "Gender", "Race",
    "A-B Average", "C-D Average", "F Average",
    "STAR Reading Grade Equivalent", "i-Ready Math Grade Level",
    "High (Kinder only)", "Medium (Kinder only)", "Low (Kinder Only)",
    "IEP", "Gifted", "ELL", "Speech Only",
}

_TEACHER_COLUMNS = {"Grade", "Teacher Name"}


def _bool(val: str) -> bool:
    return val.strip().upper() in ("1", "TRUE", "YES", "X")


def _float(val: str) -> float:
    try:
        return float(val.strip()) if val.strip() else 0.0
    except ValueError:
        return 0.0


def parse_teacher_roster(raw: bytes) -> dict[int, int]:
    """Return {grade: teacher_count} from teacher roster CSV."""
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    missing = _TEACHER_COLUMNS - set(reader.fieldnames or [])
    if missing:
        raise ValueError(f"Teacher roster missing columns: {missing}")

    counts: dict[int, int] = {}
    for row in reader:
        grade = int(row["Grade"].strip())
        counts[grade] = counts.get(grade, 0) + 1
    return counts


def parse_student_roster(raw: bytes, grade_next_col: str = "Grade Going Into") -> list[StudentRecord]:
    """Return list of StudentRecords from student roster CSV."""
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    fieldnames = set(reader.fieldnames or [])
    missing = _STUDENT_COLUMNS - fieldnames
    if missing:
        raise ValueError(f"Student roster missing columns: {missing}")

    students = []
    for i, row in enumerate(reader):
        grade_next = int(_float(row.get(grade_next_col, "0")))
        students.append(StudentRecord(
            id=str(uuid.uuid4()),
            last_name=row["Last Name"].strip(),
            first_name=row["First Name"].strip(),
            gender=row["Gender"].strip(),
            race=row["Race"].strip(),
            ab_average=_float(row["A-B Average"]),
            cd_average=_float(row["C-D Average"]),
            f_average=_float(row["F Average"]),
            star_reading=_float(row["STAR Reading Grade Equivalent"]),
            iready_math=_float(row["i-Ready Math Grade Level"]),
            kinder_high=_bool(row["High (Kinder only)"]),
            kinder_medium=_bool(row["Medium (Kinder only)"]),
            kinder_low=_bool(row["Low (Kinder Only)"]),
            iep=_bool(row["IEP"]),
            gifted=_bool(row["Gifted"]),
            ell=_bool(row["ELL"]),
            speech_only=_bool(row["Speech Only"]),
            grade_next=grade_next,
        ))
    return students


def build_grade_packets(
    teacher_raw: bytes,
    student_raw: bytes,
    weights: ObjectiveWeights,
    grades: list[int] | None = None,
) -> list[GradePacket]:
    """Parse both CSVs and return one GradePacket per requested grade."""
    teacher_counts = parse_teacher_roster(teacher_raw)
    students = parse_student_roster(student_raw)

    target_grades = grades if grades is not None else sorted(teacher_counts.keys())
    packets = []
    for grade in target_grades:
        if grade not in teacher_counts:
            raise ValueError(f"Grade {grade} not found in teacher roster")
        grade_students = [s for s in students if s.grade_next == grade]
        packets.append(GradePacket(
            grade=grade,
            students=grade_students,
            teacher_count=teacher_counts[grade],
            weights=weights,
        ))
    return packets
