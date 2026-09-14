from unittest.mock import Mock

from core.sources.multi_source import MultiSourceJobSource


def test_multi_source_combines_results():
    source1 = Mock()
    source1.search.return_value = [
        {"id": 1, "title": "GenAI Engineer", "source": "adzuna"}
    ]

    source2 = Mock()
    source2.search.return_value = [
        {"id": 2, "title": "AI Engineer", "source": "indianapi"}
    ]

    multi_source = MultiSourceJobSource(
        sources=[source1, source2]
    )

    jobs = multi_source.search("AI Engineer", "Chennai")

    assert len(jobs) == 2
    assert jobs[0]["source"] == "adzuna"
    assert jobs[1]["source"] == "indianapi"

    source1.search.assert_called_once_with(
        "AI Engineer", "Chennai"
    )
    source2.search.assert_called_once_with(
        "AI Engineer", "Chennai"
    )


def test_multi_source_continues_when_one_source_fails():
    failing_source = Mock()
    failing_source.search.side_effect = TimeoutError("API timeout")

    working_source = Mock()
    working_source.search.return_value = [
        {"id": 2, "title": "AI Engineer", "source": "indianapi"}
    ]

    multi_source = MultiSourceJobSource(
        sources=[failing_source, working_source]
    )

    jobs = multi_source.search("AI Engineer", "Chennai")

    assert len(jobs) == 1
    assert jobs[0]["source"] == "indianapi"

    failing_source.search.assert_called_once()
    working_source.search.assert_called_once()