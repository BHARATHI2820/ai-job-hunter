"""
CandidateProfile model — Phase 9.

Structured representation of section 3's skill profile. Loaded from
JSON so the profile can be updated without touching application code.
"""

from pydantic import BaseModel, Field


class CandidateProfile(BaseModel):
    genai_llm_skills: list[str] = Field(default_factory=list)
    vector_db_skills: list[str] = Field(default_factory=list)
    backend_skills: list[str] = Field(default_factory=list)
    database_skills: list[str] = Field(default_factory=list)
    ai_ml_skills: list[str] = Field(default_factory=list)
    voice_ai_skills: list[str] = Field(default_factory=list)
    dev_tools_skills: list[str] = Field(default_factory=list)

    def all_skills(self) -> list[str]:
        return (
            self.genai_llm_skills
            + self.vector_db_skills
            + self.backend_skills
            + self.database_skills
            + self.ai_ml_skills
            + self.voice_ai_skills
            + self.dev_tools_skills
        )