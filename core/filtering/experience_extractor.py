"""
Best-effort experience-range extraction from free-text job descriptions.
Adzuna doesn't return structured min/max experience, so we infer it from
common phrasings. This is a heuristic, not a guarantee — extraction
failures return (None, None), which the hard filter treats as "unknown,
do not reject" rather than a false negative.
"""

import re

# Ordered by specificity — range patterns checked before single-number patterns
_RANGE_PATTERN = re.compile(
    r"(\d+)\s*(?:-|–|to)\s*(\d+)\+?\s*years?", re.IGNORECASE
)
_PLUS_PATTERN = re.compile(r"(\d+)\+\s*years?", re.IGNORECASE)
_MINIMUM_PATTERN = re.compile(
    r"(?:minimum|at least|min\.?)\s*(\d+)\s*years?", re.IGNORECASE
)
_TOTAL_PATTERN = re.compile(r"(\d+)\s*years?\s*total", re.IGNORECASE)


def extract_experience_range(description: str | None) -> tuple[float | None, float | None]:
    if not description:
        return None, None

    match = _RANGE_PATTERN.search(description)
    if match:
        low, high = float(match.group(1)), float(match.group(2))
        return (low, high) if low <= high else (high, low)

    match = _TOTAL_PATTERN.search(description)
    if match:
        years = float(match.group(1))
        return years, years

    match = _PLUS_PATTERN.search(description)
    if match:
        years = float(match.group(1))
        return years, None  # open-ended, e.g. "8+ years"

    match = _MINIMUM_PATTERN.search(description)
    if match:
        years = float(match.group(1))
        return years, None

    return None, None