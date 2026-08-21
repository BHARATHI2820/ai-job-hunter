"""
JobSource abstraction (Phase 4).

Any real job API or permitted aggregator implements this interface.
Nothing downstream should know which concrete source is in use.
"""

from abc import ABC, abstractmethod


class JobSource(ABC):
    @abstractmethod
    def search(self, role: str, location: str) -> list[dict]:
        """Return a list of job postings matching role and location."""
        raise NotImplementedError