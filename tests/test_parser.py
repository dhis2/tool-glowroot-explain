import pytest
from pathlib import Path
from glowroot_parser import parse_glowroot_trace, generate_explain_sql, ParseError, _is_verbose, _split_verbose, _split_compact, _parse_param_list

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


def test_split_compact_extracts_sql():
    raw = "jdbc query: SELECT 1 WHERE x = ? ['hello'] => 5 rows"
    sql, _ = _split_compact(raw)
    assert sql == "SELECT 1 WHERE x = ?"


def test_split_compact_extracts_param_block():
    raw = "jdbc query: SELECT 1 WHERE x = ? ['hello'] => 5 rows"
    _, param_block = _split_compact(raw)
    assert param_block == "['hello']"


def test_split_compact_strips_jdbc_prefix_case_insensitive():
    raw = "JDBC QUERY: SELECT 1 WHERE x = ? [42] => 1 row"
    sql, _ = _split_compact(raw)
    assert sql == "SELECT 1 WHERE x = ?"


def test_split_compact_handles_multiple_params():
    raw = "jdbc query: SELECT 1 WHERE x = ? AND y = ? [42, 'abc'] => 0 rows"
    sql, param_block = _split_compact(raw)
    assert sql == "SELECT 1 WHERE x = ? AND y = ?"
    assert param_block == "[42, 'abc']"


def test_split_compact_raises_when_no_bracket():
    with pytest.raises(ParseError, match="Could not find a parameter list"):
        _split_compact("jdbc query: SELECT 1 WHERE x = 1")


def test_split_compact_works_without_row_count_suffix():
    # '=> N rows' at the end is optional
    raw = "jdbc query: SELECT 1 WHERE x = ? [42]"
    sql, param_block = _split_compact(raw)
    assert sql == "SELECT 1 WHERE x = ?"
    assert param_block == "[42]"


def test_parse_single_string():
    assert _parse_param_list("['SM2asR96Qwi']") == ["'SM2asR96Qwi'"]


def test_parse_single_integer():
    assert _parse_param_list("[42]") == ["42"]


def test_parse_single_float():
    assert _parse_param_list("[3.14]") == ["3.14"]


def test_parse_true():
    assert _parse_param_list("[true]") == ["TRUE"]


def test_parse_false():
    assert _parse_param_list("[false]") == ["FALSE"]


def test_parse_unquoted_null_uppercase():
    assert _parse_param_list("[NULL]") == ["NULL"]


def test_parse_unquoted_null_lowercase():
    assert _parse_param_list("[null]") == ["NULL"]


def test_parse_quoted_null_is_a_string():
    assert _parse_param_list("['null']") == ["'null'"]


def test_parse_mixed_string_and_integer():
    assert _parse_param_list("['130713_P6', 1]") == ["'130713_P6'", "1"]


def test_parse_string_with_comma_inside_does_not_split():
    assert _parse_param_list("['hello, world', 42]") == ["'hello, world'", "42"]


def test_parse_strings_booleans_null():
    result = _parse_param_list("['public', 'r%', true, NULL]")
    assert result == ["'public'", "'r%'", "TRUE", "NULL"]


def test_parse_empty_list():
    assert _parse_param_list("[]") == []


def test_parse_large_integer_list():
    result = _parse_param_list("[1, 2, 3, 4, 5]")
    assert result == ["1", "2", "3", "4", "5"]


def test_parse_string_with_escaped_single_quote():
    # SQL uses '' to escape a single quote inside a string
    result = _parse_param_list("['it''s a test', 42]")
    assert result == ["'it''s a test'", "42"]
