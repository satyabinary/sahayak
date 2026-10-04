from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class VisionExtraction(BaseModel):
    broker_name: str | None = Field(default=None)
    depository: str | None = Field(default=None)
    dp_id: str | None = Field(default=None)
    client_id: str | None = Field(default=None)
    confidence: dict[str, float] = Field(default_factory=dict)
    evidence_text: str = ""
    warnings: list[str] = Field(default_factory=list)


class RetrievedSource(BaseModel):
    source_name: str
    source_url: str | None = None
    document_title: str | None = None
    page_number: int | None = None
    section: str | None = None
    content: str
    score: float | None = None


class GrievanceCase(BaseModel):
    investor_name: str | None = None
    broker_name: str | None = None
    intermediary_type: str | None = None
    issue_category: str | None = None
    incident_date: str | None = None
    amount_involved: str | None = None
    transaction_details: str | None = None
    complaint_already_filed: bool | None = None
    complaint_date: str | None = None
    complaint_reference: str | None = None
    response_received: str | None = None
    evidence_available: list[str] = Field(default_factory=list)
    requested_resolution: str | None = None
    description: str | None = None


class AssistantResponse(BaseModel):
    answer: str
    sources: list[RetrievedSource] = Field(default_factory=list)
    confidence: float = 0.0


class ComplaintDraft(BaseModel):
    investor_details: dict[str, Any] = Field(default_factory=dict)
    intermediary_details: dict[str, Any] = Field(default_factory=dict)
    subject: str = ""
    summary: str = ""
    chronology: str = ""
    grievance: str = ""
    steps_taken: str = ""
    resolution_requested: str = ""
    regulatory_reference: str = ""
    declaration: str = ""
