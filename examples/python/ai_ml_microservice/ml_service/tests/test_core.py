"""Illustrative tests for the pure core -- note there are NO mocks anywhere.

Because the core does no I/O, testing it means calling functions with plain
values and asserting on plain return values. The database, config file, and
HTTP server never appear. Run with:  python -m pytest tests/  (or just read).
"""

from __future__ import annotations

from app.core.features import build_feature_vector
from app.core.types import Config, ParsedRequest
from app.core.validation import parse_request

CONFIG = Config(
    host="127.0.0.1", port=8000, model_path="artifacts/model.pkl",
    threshold=0.5, default_attendance=0.8, db_mode="inmemory", db_dsn="",
)


def test_parse_rejects_missing_applicant_id():
    result = parse_request(b'{"hours_studied": 3}')
    assert not result.ok
    assert "applicant_id" in result.error["error"]


def test_parse_accepts_valid_payload():
    result = parse_request(b'{"applicant_id": "stu-001", "hours_studied": 5, "prior_score": 0.7}')
    assert result.ok
    assert result.value == ParsedRequest("stu-001", 5.0, 0.7)


def test_missing_db_value_falls_back_to_default():
    parsed = ParsedRequest("stu-999", 4.0, 0.6)
    # attendance=None simulates "no row found"; the default is substituted.
    vector = build_feature_vector(parsed, None, CONFIG.default_attendance)
    assert vector == (4.0, 0.6, 0.8)


if __name__ == "__main__":
    test_parse_rejects_missing_applicant_id()
    test_parse_accepts_valid_payload()
    test_missing_db_value_falls_back_to_default()
    print("all core tests passed (no mocks needed)")
