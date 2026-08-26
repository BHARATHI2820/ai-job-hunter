"""
Loads CandidateProfile from JSON. Section 3: must be editable without
modifying application code.
"""

import json
from pathlib import Path

from core.profile.candidate_profile import CandidateProfile

_PROFILE_PATH = Path(__file__).parent / "profile.json"


def load_profile() -> CandidateProfile:
    with open(_PROFILE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return CandidateProfile(**data)