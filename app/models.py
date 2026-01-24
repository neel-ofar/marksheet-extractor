# app/models.py
from typing import List, Optional
from pydantic import BaseModel, Field


class FieldValue(BaseModel):
    """Single extracted field with confidence"""
    value: str = Field(..., description="Extracted value (empty string if not found)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0.0–1.0")


class CandidateDetails(BaseModel):
    """Personal & exam identification information"""
    name: FieldValue
    father_name: Optional[FieldValue] = None
    mother_name: Optional[FieldValue] = None
    roll_no: FieldValue
    registration_no: Optional[FieldValue] = None
    dob: Optional[FieldValue] = Field(None, description="Date of birth – prefer YYYY-MM-DD")
    exam_year: FieldValue
    board_university: FieldValue
    institution: Optional[FieldValue] = None


class Subject(BaseModel):
    """One subject row from the marks table"""
    subject: str = Field(..., description="Subject name")
    max_marks: Optional[str] = None
    obtained_marks: Optional[str] = None
    credits: Optional[str] = None
    grade: Optional[str] = None
    confidence: float = Field(..., ge=0.0, le=1.0)


class OverallResult(BaseModel):
    """Aggregate result information"""
    result: FieldValue                     # e.g. "Pass", "Fail", "Promoted"
    grade: Optional[FieldValue] = None     # e.g. "A", "First Division"
    division: Optional[FieldValue] = None  # e.g. "First", "Second"
    percentage: Optional[FieldValue] = None
    total_max_marks: Optional[FieldValue] = None
    total_obtained_marks: Optional[FieldValue] = None


class IssueInfo(BaseModel):
    """Issuance details if visible"""
    date: Optional[FieldValue] = None
    place: Optional[FieldValue] = None


class ExtractionResult(BaseModel):
    """Complete structured output of one marksheet"""
    candidate_details: CandidateDetails
    subjects: List[Subject]
    overall: OverallResult
    issue: Optional[IssueInfo] = None
    bounding_boxes: Optional[dict[str, str]] = Field(
        None,
        description="Optional approximate regions e.g. {'name': 'top-center', 'subjects': 'middle'}"
    )
    page_count: int = Field(1, description="Number of pages processed (for PDFs)")
    model_used: str = Field("llama-3.2-11b-vision-preview", description="LLM model identifier")


class BatchExtractionItem(BaseModel):
    """One item in batch response"""
    filename: str
    success: bool
    extraction: Optional[ExtractionResult] = None
    error: Optional[str] = None
