from pydantic import BaseModel
from typing import List, Literal


class Parameter(BaseModel):
    name: str
    value: float
    unit: str
    category: str
    status: Literal["normal", "high", "low", "unknown"]


class CategorySummary(BaseModel):
    blood: str
    diabetes: str
    cardio: str
    urine: str
    weight: str
    thyroid: str


class ReportResponse(BaseModel):
    report_type: Literal["multi"] = "multi"
    parameters: List[Parameter]
    overall_status: str
    key_findings: List[str]
    category_summary: CategorySummary
    recommendation: str
    summary_text: str
