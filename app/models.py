from __future__ import annotations
from pydantic import BaseModel


class StudentRecord(BaseModel):
    id: str
    last_name: str
    first_name: str
    gender: str
    race: str
    ab_average: float = 0.0
    cd_average: float = 0.0
    f_average: float = 0.0
    star_reading: float = 0.0
    iready_math: float = 0.0
    kinder_high: bool = False
    kinder_medium: bool = False
    kinder_low: bool = False
    iep: bool = False
    gifted: bool = False
    ell: bool = False
    speech_only: bool = False
    grade_current: int = 0
    grade_next: int = 0


class GradePacket(BaseModel):
    grade: int
    students: list[StudentRecord]
    teacher_count: int
    weights: ObjectiveWeights


class ObjectiveWeights(BaseModel):
    iep: float = 3.0
    academic: float = 2.0
    gender: float = 1.0
    gifted: float = 1.0
    ell: float = 1.0
    speech_only: float = 1.0


class AssignmentResult(BaseModel):
    grade: int
    assignments: dict[str, int]  # student_id -> classroom index (0-based)
    solver_status: str
    solve_time_seconds: float
