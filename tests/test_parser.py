import pytest
from pathlib import Path
from glowroot_parser import parse_glowroot_trace, generate_explain_sql, ParseError, _is_verbose

FIXTURES = Path(__file__).parent / "fixtures"


def load(name: str) -> str:
    return (FIXTURES / name).read_text()


DEFAULT_OPTIONS = {
    "analyze": False, "verbose": False, "costs": True, "settings": False,
    "memory": False, "generic_plan": False, "buffers": False, "timing": False,
    "wal": False, "summary": False, "format": "TEXT",
}

ANALYZE_OPTIONS = {
    **DEFAULT_OPTIONS, "analyze": True, "buffers": True, "timing": True, "summary": True, "costs": False,
}


def test_verbose_detected_from_parameters_line():
    raw = "jdbc query:\nSELECT 1\n\nparameters:\n\n  [42]\n\nrows:\n\n  => 1 row"
    assert _is_verbose(raw) is True


def test_compact_has_no_parameters_line():
    raw = "jdbc query: SELECT 1 WHERE x = ? [42] => 1 row"
    assert _is_verbose(raw) is False


def test_parameters_inside_sql_string_does_not_trigger_verbose():
    # 'parameters:' appears in a SQL string literal, not on its own line
    raw = "jdbc query: SELECT * FROM t WHERE col = 'parameters: foo' [42] => 0 rows"
    assert _is_verbose(raw) is False
