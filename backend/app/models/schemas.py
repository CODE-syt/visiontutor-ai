"""
Pydantic schemas: the contract between the LLM's JSON output, the backend,
and the React frontend. Every field the AI is asked to produce is validated
here before it ever reaches the client.
"""
from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class InterviewQuestion(BaseModel):
    question: str
    answer: str


class AnalysisResult(BaseModel):
    image_type: str = Field(default="general_image")
    concept: str = Field(default="Unknown")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)

    image_summary: str = ""
    extracted_text: List[str] = Field(default_factory=list)
    visual_elements: List[str] = Field(default_factory=list)

    beginner_explanation: str = ""
    technical_explanation: str = ""
    step_by_step: List[str] = Field(default_factory=list)
    how_it_works: List[str] = Field(default_factory=list)

    formula: str = ""
    real_world_example: str = ""
    advantages: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    related_concepts: List[str] = Field(default_factory=list)

    interview_answer: str = ""
    interview_questions: List[InterviewQuestion] = Field(default_factory=list)

    rag_context_used: bool = False

    @field_validator("confidence", mode="before")
    @classmethod
    def clamp_confidence(cls, v):
        try:
            v = float(v)
        except (TypeError, ValueError):
            return 0.0
        return max(0.0, min(1.0, v))


class AnalyzeResponse(BaseModel):
    success: bool = True
    result: Optional[AnalysisResult] = None
    error: Optional[str] = None


class FollowUpRequest(BaseModel):
    """Used for the 'chat with the uploaded image' follow-up feature."""
    analysis_id: Optional[str] = None
    previous_result: AnalysisResult
    question: str


class FollowUpResponse(BaseModel):
    success: bool = True
    answer: str = ""
    error: Optional[str] = None


class HealthResponse(BaseModel):
    status: str = "healthy"


class HistoryItem(BaseModel):
    id: str
    concept: str
    confidence: float
    timestamp: str


class HistoryListResponse(BaseModel):
    items: List[HistoryItem] = Field(default_factory=list)
