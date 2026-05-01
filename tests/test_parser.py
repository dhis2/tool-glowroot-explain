import pytest
from pathlib import Path
from glowroot_parser import parse_glowroot_trace, generate_explain_sql, ParseError, _is_verbose, _split_verbose, _split_compact, _parse_param_list, _substitute, _build_explain_clause, _is_dml

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


def test_parse_unterminated_string_raises():
    with pytest.raises(ParseError, match="Unterminated string"):
        _parse_param_list("['no closing quote, 42]")


def test_substitute_single_string():
    assert _substitute("WHERE x = ?", ["'hello'"]) == "WHERE x = 'hello'"


def test_substitute_multiple_params_left_to_right():
    assert _substitute("WHERE a = ? AND b = ?", ["1", "'two'"]) == "WHERE a = 1 AND b = 'two'"


def test_substitute_null():
    assert _substitute("WHERE x = ?", ["NULL"]) == "WHERE x = NULL"


def test_substitute_boolean():
    assert _substitute("WHERE active = ?", ["TRUE"]) == "WHERE active = TRUE"


def test_substitute_raises_too_few_params():
    with pytest.raises(ParseError, match=r"SQL has 2 '\?' placeholders but only 1 parameters were found"):
        _substitute("WHERE a = ? AND b = ?", ["1"])


def test_substitute_raises_too_many_params():
    with pytest.raises(ParseError, match=r"Found 2 parameters but SQL only has 1 '\?' placeholders"):
        _substitute("WHERE a = ?", ["1", "2"])


def test_substitute_raises_empty_params_with_placeholders():
    with pytest.raises(ParseError, match=r"SQL has 1 '\?' placeholders but the parameter list is empty"):
        _substitute("WHERE a = ?", [])


def test_substitute_no_placeholders_no_params_is_valid():
    assert _substitute("SELECT 1", []) == "SELECT 1"


def test_substitute_param_containing_question_mark():
    assert _substitute("WHERE a = ? AND b = ?", ["'what?'", "42"]) == "WHERE a = 'what?' AND b = 42"


_ALL_OFF = {k: False for k in ["analyze","verbose","costs","settings","memory","generic_plan","buffers","timing","wal","summary"]}


def test_explain_clause_no_boolean_options():
    opts = {**_ALL_OFF, "format": "TEXT"}
    assert _build_explain_clause(opts) == "EXPLAIN (FORMAT TEXT)"


def test_explain_clause_costs_only():
    opts = {**_ALL_OFF, "costs": True, "format": "TEXT"}
    assert _build_explain_clause(opts) == "EXPLAIN (COSTS, FORMAT TEXT)"


def test_explain_clause_analyze_buffers_timing():
    opts = {**_ALL_OFF, "analyze": True, "buffers": True, "timing": True, "format": "TEXT"}
    assert _build_explain_clause(opts) == "EXPLAIN (ANALYZE, BUFFERS, TIMING, FORMAT TEXT)"


def test_explain_clause_canonical_order():
    # All boolean options on except GENERIC_PLAN — verify table order from spec
    opts = {**_ALL_OFF, "analyze": True, "verbose": True, "costs": True, "settings": True,
            "memory": True, "buffers": True, "timing": True, "wal": True, "summary": True, "format": "JSON"}
    assert _build_explain_clause(opts) == "EXPLAIN (ANALYZE, VERBOSE, COSTS, SETTINGS, MEMORY, BUFFERS, TIMING, WAL, SUMMARY, FORMAT JSON)"


def test_explain_clause_format_json():
    opts = {**_ALL_OFF, "format": "JSON"}
    assert _build_explain_clause(opts) == "EXPLAIN (FORMAT JSON)"


def test_explain_clause_format_always_last():
    opts = {**_ALL_OFF, "verbose": True, "format": "YAML"}
    assert _build_explain_clause(opts).endswith("FORMAT YAML)")


def test_select_is_not_dml():
    assert _is_dml("SELECT 1") is False


def test_delete_is_dml():
    assert _is_dml("DELETE FROM foo WHERE id = 1") is True


def test_insert_is_dml():
    assert _is_dml("INSERT INTO foo VALUES (1)") is True


def test_update_is_dml():
    assert _is_dml("UPDATE foo SET x = 1") is True


def test_merge_is_dml():
    assert _is_dml("MERGE INTO foo USING bar ON foo.id = bar.id") is True


def test_truncate_is_dml():
    assert _is_dml("TRUNCATE TABLE foo") is True


def test_execute_is_dml():
    assert _is_dml("EXECUTE my_prepared_plan") is True


def test_create_table_as_is_dml():
    assert _is_dml("CREATE TABLE foo AS SELECT 1") is True


def test_plain_create_table_is_not_dml():
    # CREATE TABLE without AS is plain DDL — should not be wrapped
    assert _is_dml("CREATE TABLE foo (id int)") is False


def test_dml_detection_is_case_insensitive():
    assert _is_dml("delete from foo") is True


def test_dml_detection_ignores_leading_whitespace():
    assert _is_dml("  \n  DELETE FROM foo") is True


def test_delete_with_analyze_wraps_in_transaction():
    result = generate_explain_sql(
        "DELETE FROM foo WHERE id = 1",
        [],
        {**ANALYZE_OPTIONS, "costs": False},
    )
    assert result == (
        "-- Statement type may modify data: wrapped in transaction for safety\n"
        "BEGIN;\n"
        "EXPLAIN (ANALYZE, BUFFERS, TIMING, SUMMARY, FORMAT TEXT)\n"
        "DELETE FROM foo WHERE id = 1;\n"
        "ROLLBACK;"
    )


def test_select_with_analyze_is_not_wrapped():
    result = generate_explain_sql(
        "SELECT 1 WHERE x = ?",
        ["42"],
        {**ANALYZE_OPTIONS, "costs": False},
    )
    assert "BEGIN;" not in result
    assert "ROLLBACK;" not in result


def test_delete_without_analyze_is_not_wrapped():
    result = generate_explain_sql(
        "DELETE FROM foo WHERE id = 1",
        [],
        {**DEFAULT_OPTIONS},
    )
    assert "BEGIN;" not in result
    assert "ROLLBACK;" not in result


def test_integration_compact_single_string():
    raw = load("compact_single_string.txt")
    sql, params = parse_glowroot_trace(raw)
    assert params == ["'SM2asR96Qwi'"]
    assert sql.count('?') == 1
    result = generate_explain_sql(sql, params, DEFAULT_OPTIONS)
    assert "'SM2asR96Qwi'" in result
    assert '?' not in result


def test_integration_verbose_string_and_integer():
    raw = load("verbose_string_integer.txt")
    sql, params = parse_glowroot_trace(raw)
    assert params == ["'130713_P6'", "1"]
    assert sql.count('?') == 2
    result = generate_explain_sql(sql, params, DEFAULT_OPTIONS)
    assert "'130713_P6'" in result
    assert '?' not in result


def test_integration_verbose_strings_and_booleans():
    raw = load("verbose_strings_booleans.txt")
    sql, params = parse_glowroot_trace(raw)
    assert "TRUE" in params
    assert "'in3pSeq1UNJ'" == params[-1]
    assert sql.count('?') == len(params)
    result = generate_explain_sql(sql, params, DEFAULT_OPTIONS)
    assert '?' not in result
    assert "TRUE" in result


def test_integration_verbose_with_null():
    raw = load("verbose_with_null.txt")
    sql, params = parse_glowroot_trace(raw)
    assert params[-1] == "NULL"
    assert sql.count('?') == len(params)
    result = generate_explain_sql(sql, params, DEFAULT_OPTIONS)
    assert '?' not in result
    # last substituted value is NULL, followed by ;
    assert result.rstrip().endswith("NULL;")


def test_integration_compact_64_integer_params():
    raw = load("compact_large_integers.txt")
    sql, params = parse_glowroot_trace(raw)
    assert len(params) == 64
    assert all(p.isdigit() for p in params)
    result = generate_explain_sql(sql, params, DEFAULT_OPTIONS)
    assert '?' not in result
    assert "385870" in result


def test_integration_empty_input_raises():
    with pytest.raises(ParseError, match="Paste a Glowroot JDBC trace above"):
        parse_glowroot_trace("")


def test_integration_no_param_block_raises():
    with pytest.raises(ParseError, match="Could not find a parameter list"):
        parse_glowroot_trace("jdbc query: SELECT 1 WHERE x = 1")
