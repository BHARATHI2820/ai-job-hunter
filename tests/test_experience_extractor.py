from core.filtering.experience_extractor import extract_experience_range


def test_extract_range():
    assert extract_experience_range("1-3 years") == (1.0, 3.0)


def test_extract_range_with_to():
    assert extract_experience_range("1 to 3 years") == (1.0, 3.0)


def test_extract_plus_years():
    assert extract_experience_range("2+ years") == (2.0, None)


def test_extract_minimum_years():
    assert extract_experience_range("minimum 2 years") == (2.0, None)


def test_extract_at_least_years():
    assert extract_experience_range("at least 3 years") == (3.0, None)


def test_extract_total_years():
    assert extract_experience_range("3 years total") == (3.0, 3.0)


def test_extract_decimal_range():
    assert extract_experience_range("1.5-3 years") == (1.5, 3.0)


def test_unknown_experience():
    assert extract_experience_range("Python developer") == (None, None)


def test_empty_description():
    assert extract_experience_range(None) == (None, None)