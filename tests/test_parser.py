import pytest
from pathlib import Path
from glowroot_parser import parse_glowroot_trace, generate_explain_sql, ParseError, _is_verbose, _split_verbose

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


def test_split_verbose_extracts_sql():
    raw = "jdbc query:\n\nSELECT 1 WHERE x = ?\n\nparameters:\n\n  ['hello']\n\nrows:\n\n  => 1 row"
    sql, param_block = _split_verbose(raw)
    assert sql == "SELECT 1 WHERE x = ?"


def test_split_verbose_extracts_param_block():
    raw = "jdbc query:\n\nSELECT 1 WHERE x = ?\n\nparameters:\n\n  ['hello']\n\nrows:\n\n  => 1 row"
    _, param_block = _split_verbose(raw)
    assert param_block == "['hello']"


def test_split_verbose_strips_jdbc_prefix_case_insensitive():
    raw = "JDBC QUERY:\n\nSELECT 1\n\nparameters:\n\n  [42]\n\nrows:\n\n  => 1 row"
    sql, _ = _split_verbose(raw)
    assert sql == "SELECT 1"


def test_split_verbose_preserves_multiline_sql():
    raw = "jdbc query:\n\nSELECT a,\n       b\n  FROM t\n WHERE x = ?\n\nparameters:\n\n  [1]\n\nrows:\n\n  => 0 rows"
    sql, _ = _split_verbose(raw)
    assert "SELECT a," in sql
    assert "WHERE x = ?" in sql


def test_split_verbose_not_confused_by_parameters_alias_in_sql_body():
    # 'parameters:' appears as a column alias inside the SQL but the real
    # section marker is still correctly found and split on
    raw = "jdbc query:\n\nSELECT col AS \"parameters:\", x\n  FROM t\n WHERE y = ?\n\nparameters:\n\n  [1]\n\nrows:\n\n  => 0 rows"
    sql, param_block = _split_verbose(raw)
    assert param_block == "[1]"


def test_split_verbose_works_without_rows_section():
    raw = "jdbc query:\n\nSELECT 1\n\nparameters:\n\n  [42]\n"
    sql, param_block = _split_verbose(raw)
    assert sql == "SELECT 1"
    assert param_block == "[42]"
