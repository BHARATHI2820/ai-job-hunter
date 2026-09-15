from datetime import datetime, UTC
from typing import Literal

from pydantic import BaseModel, Field


class Job(BaseModel):
    id: str
    title: str
    company: str | None = None
    location: str | None = None
    work_mode: str | None = None
    description: str | None = None
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    experience_text: str | None = None
    experience_min: int | None = None
    experience_max: int | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    currency: str = "INR"
    source: str
    source_job_id: str
    job_url: str | None = None
    posted_date: datetime | None = None
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    active_status: Literal["active", "inactive", "unknown"] = "unknown"
    active_status_reason: str | None = None
    matched_skills: list[str] = Field(default_factory=list)
    skill_match_score: float | None = None
    experience_fit_score: float | None = None
    semantic_match_score: float | None = None
    relevance_score: float | None = None
    match_explanation: str | None = None