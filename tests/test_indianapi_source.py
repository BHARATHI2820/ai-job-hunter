from unittest.mock import Mock, patch
import pytest

from core.sources.indianapi_source import IndianAPISource


def test_indianapi_source_maps_jobs(monkeypatch):
    monkeypatch.setenv("INDIANAPI_JOBS_API_KEY", "test-key")

    fake_response = Mock()
    fake_response.raise_for_status.return_value = None
    fake_response.json.return_value = [
        {
            "id": 123,
            "title": "GenAI Engineer",
            "company": "Test Company",
            "location": "Chennai",
            "job_description": "Build GenAI applications.",
            "experience": "1-3 years",
            "apply_link": "https://example.com/job/123",
            "posted_date": "2026-09-10T10:00:00",
        }
    ]

    with patch(
        "core.sources.indianapi_source.requests.get",
        return_value=fake_response,
    ) as mock_get:
        source = IndianAPISource()
        jobs = source.search("GenAI Engineer", "Chennai")

    assert len(jobs) == 1

    job = jobs[0]

    assert job["id"] == 123
    assert job["title"] == "GenAI Engineer"
    assert job["company"] == "Test Company"
    assert job["location"] == "Chennai"
    assert job["description"] == "Build GenAI applications."
    assert job["experience"] == "1-3 years"
    assert job["job_url"] == "https://example.com/job/123"
    assert job["source"] == "indianapi"

    mock_get.assert_called_once()


def test_indianapi_source_requires_api_key(monkeypatch):
    monkeypatch.delenv("INDIANAPI_JOBS_API_KEY", raising=False)

    try:
        IndianAPISource()
        assert False, "Expected ValueError when API key is missing"
    except ValueError as exc:
        assert "INDIANAPI_JOBS_API_KEY" in str(exc)


def test_indianapi_source_returns_empty_for_invalid_response(monkeypatch):
    monkeypatch.setenv("INDIANAPI_JOBS_API_KEY", "test-key")

    fake_response = Mock()
    fake_response.raise_for_status.return_value = None
    fake_response.json.return_value = {"jobs": []}

    with patch(
        "core.sources.indianapi_source.requests.get",
        return_value=fake_response,
    ):
        source = IndianAPISource()
        jobs = source.search("GenAI Engineer", "Chennai")

    assert jobs == []

def test_indianapi_429_not_retried(monkeypatch):
    """429 should fail fast — no retry delay for quota exhaustion."""
    import requests
    from core.sources.indianapi_source import IndianAPISource

    call_count = {"n": 0}

    def fake_get(*args, **kwargs):
        call_count["n"] += 1
        response = requests.Response()
        response.status_code = 429
        return response

    monkeypatch.setenv("INDIANAPI_JOBS_API_KEY", "dummy")
    monkeypatch.setattr(requests, "get", fake_get)

    source = IndianAPISource()
    with pytest.raises(requests.exceptions.HTTPError):
        source.search("GenAI Engineer", "Chennai")

    assert call_count["n"] == 1  # no retry attempted for 429