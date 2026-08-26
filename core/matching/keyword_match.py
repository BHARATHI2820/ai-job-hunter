"""
Deterministic keyword-level skill matching — Phase 9.

Exact, case-insensitive substring matching. Known limitation: will NOT
catch typos or paraphrased skills (e.g. a real posting in this project's
own data contains "LangChan" instead of "LangChain" — exact matching
misses this by design). Semantic matching in Phase 10 addresses that gap.
"""

from core.models.job import Job
from core.profile.candidate_profile import CandidateProfile


def score_job_against_profile(job: Job, profile: CandidateProfile) -> tuple[list[str], float]:
    searchable_text = f"{job.title or ''} {job.description or ''}".lower()

    all_skills = profile.all_skills()
    matched = [skill for skill in all_skills if skill.lower() in searchable_text]

    score = (len(matched) / len(all_skills)) * 100 if all_skills else 0.0
    return matched, round(score, 1)