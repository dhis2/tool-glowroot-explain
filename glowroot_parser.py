import re


class ParseError(ValueError):
    pass


_OPTION_ORDER = [
    "analyze", "verbose", "costs", "settings", "memory", "generic_plan",
    "buffers", "timing", "wal", "summary",
]

_DML_FIRST_WORDS = {"insert", "update", "delete", "merge", "truncate", "execute"}


def _is_verbose(raw: str) -> bool:
    return bool(re.search(r'^\s*parameters:\s*$', raw, re.MULTILINE))


def _split_verbose(raw: str) -> tuple[str, str]:
    text = re.sub(r'(?i)^\s*jdbc\s+query:\s*', '', raw.strip(), count=1)
    parts = re.split(r'^\s*parameters:\s*$', text, maxsplit=1, flags=re.MULTILINE)
    sql = parts[0].strip()
    rest = parts[1] if len(parts) > 1 else ''
    rows_split = re.split(r'^\s*rows:\s*$', rest, maxsplit=1, flags=re.MULTILINE)
    param_block = rows_split[0].strip()
    return sql, param_block


def _split_compact(raw: str) -> tuple[str, str]:
    text = re.sub(r'(?i)^\s*jdbc\s+query:\s*', '', raw.strip(), count=1)
    text = re.sub(r'=>\s*\d+\s+rows?\s*$', '', text).strip()
    # rfind finds the last '[' — assumes no string parameter value contains '['.
    # SQL-side brackets (array subscripts, JSON operators) always appear before the param block.
    bracket_start = text.rfind('[')
    if bracket_start == -1:
        return text, '[]'
    bracket_end = text.find(']', bracket_start)
    if bracket_end == -1:
        raise ParseError("Could not find a parameter list '[...]' in the trace.")
    sql = text[:bracket_start].strip()
    param_block = text[bracket_start:bracket_end + 1]
    return sql, param_block


def _parse_param_list(param_block: str) -> list[str]:
    content = param_block.strip()
    if content.startswith('['):
        content = content[1:]
    if content.endswith(']'):
        content = content[:-1]
    content = content.strip()
    if not content:
        return []

    params: list[str] = []
    i = 0
    while i < len(content):
        if content[i] in ' \t':
            i += 1
        elif content[i] == ',':
            i += 1
        elif content[i] == "'":
            j = i + 1
            while j < len(content):
                if content[j] == "'":
                    if j + 1 < len(content) and content[j + 1] == "'":
                        j += 2  # '' is an escaped single quote — skip both chars
                        continue
                    break
                j += 1
            if j >= len(content):
                raise ParseError(f"Unterminated string literal in parameter block at position {i}.")
            params.append(content[i:j + 1])
            i = j + 1
        else:
            j = i
            while j < len(content) and content[j] != ',':
                j += 1
            val = content[i:j].strip()
            if val.lower() == 'true':
                params.append('TRUE')
            elif val.lower() == 'false':
                params.append('FALSE')
            elif val.lower() == 'null':
                params.append('NULL')
            elif re.match(r'^-?\d+(\.\d+)?$', val):
                params.append(val)
            else:
                params.append(f"'{val}'")
            i = j
    return params


def _substitute(sql: str, params: list[str]) -> str:
    count = sql.count('?')
    if count > 0 and len(params) == 0:
        raise ParseError(f"SQL has {count} '?' placeholders but the parameter list is empty.")
    if count > len(params):
        raise ParseError(f"SQL has {count} '?' placeholders but only {len(params)} parameters were found.")
    if len(params) > count:
        raise ParseError(f"Found {len(params)} parameters but SQL only has {count} '?' placeholders.")
    parts = sql.split('?')
    return ''.join(part + param for part, param in zip(parts, params)) + parts[-1]


def _build_explain_clause(options: dict) -> str:
    parts = [k.upper() for k in _OPTION_ORDER if options.get(k)]
    parts.append(f"FORMAT {options.get('format', 'TEXT').upper()}")
    return f"EXPLAIN ({', '.join(parts)})"


def _is_dml(sql: str) -> bool:
    words = sql.strip().lower().split()
    if not words:
        return False
    if words[0] in _DML_FIRST_WORDS:
        return True
    # Only "CREATE TABLE ... AS (SELECT ...)" is DML — plain DDL "CREATE TABLE foo (...)" is not
    if len(words) >= 3 and words[0] == "create" and words[1] == "table":
        return any(w == "as" for w in words[3:])
    return False


def parse_glowroot_trace(raw: str) -> tuple[str, list[str]]:
    if not raw.strip():
        raise ParseError("Paste a Glowroot JDBC trace above.")
    if _is_verbose(raw):
        sql, param_block = _split_verbose(raw)
    else:
        sql, param_block = _split_compact(raw)
    if not sql.strip():
        raise ParseError("No SQL found in the trace.")
    params = _parse_param_list(param_block)
    return sql, params


def generate_explain_sql(sql: str, params: list[str], options: dict) -> str:
    if not sql.strip():
        raise ParseError("No SQL found in the trace.")
    substituted = _substitute(sql, params)
    clause = _build_explain_clause(options)
    explain = f"{clause}\n{substituted};"
    if options.get("analyze") and _is_dml(substituted):
        explain = (
            "-- Statement type may modify data: wrapped in transaction for safety\n"
            f"BEGIN;\n{explain}\nROLLBACK;"
        )
    return explain
