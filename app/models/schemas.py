from pydantic import BaseModel
from typing import Optional


class SlotML(BaseModel):
    id: str
    class_name: str = ""
    subject: str = ""
    day: str = ""
    time_slot: str = ""
    room: str = ""
    teacher: str = ""
    week_number: int = 1


class TeacherML(BaseModel):
    id: str
    name: str
    max_daily_hours: float = 8.0
    off_days: list[str] = []
    subjects: list[str] = []


class PredictRequest(BaseModel):
    schedule_id: str
    slots: list[SlotML]
    teachers: list[TeacherML]


class MLConflict(BaseModel):
    type: str
    severity: str
    description: str
    slot_ids: list[str] = []
    confidence: float = 1.0


class PredictResponse(BaseModel):
    conflicts: list[MLConflict]


class ResolveRequest(BaseModel):
    conflict_id: str
    context: dict


class Alternative(BaseModel):
    rank: int
    confidence: float
    changes: list[dict]
    explanation: str


class ResolveResponse(BaseModel):
    alternatives: list[Alternative]


class ExplainRequest(BaseModel):
    conflict_id: str
    context: dict


class ExplainResponse(BaseModel):
    explanation: str
    reasoning_steps: list[str] = []


class QueryRequest(BaseModel):
    query: str
    schedule_id: str


class QueryResponse(BaseModel):
    answer: str
    result_data: Optional[dict] = None
