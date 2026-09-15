"""
Best-effort experience-range extraction.

Supports experience information coming from:
- free-text job descriptions
- structured experience text from job sources such as IndianAPI

Extraction failures return (None, None).
"""

import re


# Range examples:
# "1-3 years"
# "1 – 3 years"
# "1 to 3 years"
_RANGE_PATTERN = re.compile(
    r"(\d+(?:\.\d+)?)\s*(?:-|–|to)\s*(\d+(?:\.\d+)?)\s*\+?\s*years?",
    re.IGNORECASE,
)


# Open-ended examples:
# "2+ years"
# "2.5+ years"
_PLUS_PATTERN = re.compile(
    r"(\d+(?:\.\d+)?)\s*\+\s*years?",
    re.IGNORECASE,
)


# Examples:
# "minimum 2 years"
# "at least 2 years"
# "min. 2 years"
_MINIMUM_PATTERN = re.compile(
    r"(?:minimum|at least|min\.?)\s*(\d+(?:\.\d+)?)\s*years?",
    re.IGNORECASE,
)


# Example:
# "3 years total"
_TOTAL_PATTERN = re.compile(
    r"(\d+(?:\.\d+)?)\s*years?\s*total",
    re.IGNORECASE,
)


def extract_experience_range(
    description: str | None,
) -> tuple[float | None, float | None]:
    """
    Extract minimum and maximum experience from free text.

    Returns:
        (minimum, maximum)

    Examples:
        "1-3 years"      -> (1.0, 3.0)
        "2+ years"       -> (2.0, None)
        "minimum 2 years" -> (2.0, None)
        "3 years total"  -> (3.0, 3.0)
        unknown text     -> (None, None)
    """

    if not description:
        return None, None

    match = _RANGE_PATTERN.search(description)

    if match:
        low = float(match.group(1))
        high = float(match.group(2))

        return (low, high) if low <= high else (high, low)

    match = _TOTAL_PATTERN.search(description)

    if match:
        years = float(match.group(1))
        return years, years

    match = _PLUS_PATTERN.search(description)

    if match:
        years = float(match.group(1))
        return years, None

    match = _MINIMUM_PATTERN.search(description)

    if match:
        years = float(match.group(1))
        return years, None

    return None, None