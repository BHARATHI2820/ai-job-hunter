"""
Experience fit scoring — Phase 17.

Calculates how well a candidate's experience fits a job's
extracted experience range.
"""

from core.models.job import Job


UNKNOWN_FIT_SCORE = 50.0
STRONG_FIT_SCORE = 100.0
SLIGHTLY_BELOW_SCORE = 70.0
OVERQUALIFIED_SCORE = 90.0
NO_FIT_SCORE = 0.0


def calculate_experience_fit(
    job: Job,
    candidate_experience_years: float,
) -> float:
    """
    Calculate how well the candidate's experience fits the job.

    Unknown job experience is treated as neutral (50).
    """

    minimum = job.experience_min
    maximum = job.experience_max

    if minimum is None:
        return UNKNOWN_FIT_SCORE

    # Open-ended requirement such as "8+ years".
    if maximum is None:
        if candidate_experience_years >= minimum:
            return STRONG_FIT_SCORE
        if minimum - candidate_experience_years <= 1:
            return SLIGHTLY_BELOW_SCORE
        return NO_FIT_SCORE

    # Candidate is within the stated range.
    if minimum <= candidate_experience_years <= maximum:
        return STRONG_FIT_SCORE

    # Candidate is below the minimum, but only slightly.
    if candidate_experience_years < minimum:
        if minimum - candidate_experience_years <= 1:
            return SLIGHTLY_BELOW_SCORE
        return NO_FIT_SCORE

    # Candidate is above the stated maximum.
    return OVERQUALIFIED_SCORE