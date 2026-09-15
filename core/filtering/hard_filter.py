"""
Hard filtering — Phase 8.

Deterministic rejection BEFORE any LLM involvement, per section 14.
Config is a plain dataclass, not hardcoded thresholds, per section 2.
"""

from dataclasses import dataclass

from core.filtering.experience_extractor import extract_experience_range
from core.models.job import Job


@dataclass
class HardFilterConfig:
    candidate_experience_years: float = 1.3
    experience_buffer_years: float = 2.0  # how far above actual experience is still acceptable
    requested_location: str = "Chennai"
    allow_remote: bool = True

    @property
    def max_acceptable_job_min_experience(self) -> float:
        return self.candidate_experience_years + self.experience_buffer_years


def _fails_experience(job: Job, config: HardFilterConfig) -> str | None:
    experience_source = job.experience_text or job.description
    exp_min, exp_max = extract_experience_range(experience_source)
    job.experience_min = exp_min
    job.experience_max = exp_max

    if exp_min is None:
        return None  # unknown — do not reject, per section 14's "obviously senior" standard

    if exp_min > config.max_acceptable_job_min_experience:
        return (
            f"Requires {exp_min:.0f}+ years experience, "
            f"exceeds acceptable range (candidate: {config.candidate_experience_years} "
            f"years, buffer: {config.experience_buffer_years} years)"
        )
    return None


def _fails_location(job: Job, config: HardFilterConfig) -> str | None:
    if not job.location:
        return None  # unknown — do not reject

    location_lower = job.location.lower()
    requested_lower = config.requested_location.lower()

    if requested_lower in location_lower:
        return None
    if config.allow_remote and "remote" in location_lower:
        return None

    return f"Location '{job.location}' does not match requested '{config.requested_location}'"


def apply_hard_filters(
    jobs: list[Job], config: HardFilterConfig
) -> tuple[list[Job], list[tuple[Job, str]]]:
    kept: list[Job] = []
    rejected: list[tuple[Job, str]] = []

    for job in jobs:
        reason = _fails_experience(job, config) or _fails_location(job, config)
        if reason:
            rejected.append((job, reason))
        else:
            kept.append(job)

    if rejected:
        print(f"[HARD FILTER] Rejected {len(rejected)} job(s):")
        for job, reason in rejected:
            print(f"    - {job.title} @ {job.company}: {reason}")

    return kept, rejected