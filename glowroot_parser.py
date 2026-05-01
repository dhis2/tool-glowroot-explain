import re


class ParseError(ValueError):
    pass


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


def parse_glowroot_trace(raw: str) -> tuple[str, list[str]]:
    raise NotImplementedError


def generate_explain_sql(sql: str, params: list[str], options: dict) -> str:
    raise NotImplementedError
