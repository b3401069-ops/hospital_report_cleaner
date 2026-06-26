from report_cleaner.cleaner import _normalize_date_value, _normalize_period_token


def test_normalize_date_value_handles_roc_dates() -> None:
    assert _normalize_date_value("1140101") == "2025-01-01"
    assert _normalize_date_value("11401011230") == "2025-01-01 12:30"


def test_normalize_date_value_handles_western_dates() -> None:
    assert _normalize_date_value("20250101") == "2025-01-01"
    assert _normalize_date_value("20250101123000") == "2025-01-01 12:30:00"


def test_normalize_date_value_preserves_empty_and_unknown_values() -> None:
    assert _normalize_date_value("") == ""
    assert _normalize_date_value("not a date") == "not a date"


def test_normalize_period_token_handles_months_and_roc_dates() -> None:
    assert _normalize_period_token("202501", is_end=False) == "2025-01-01"
    assert _normalize_period_token("202501", is_end=True) == "2025-01-31"
    assert _normalize_period_token("1140101", is_end=False) == "2025-01-01"
