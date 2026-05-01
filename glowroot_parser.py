import re


class ParseError(ValueError):
    pass


def _is_verbose(raw: str) -> bool:
    return bool(re.search(r'^\s*parameters:\s*$', raw, re.MULTILINE))


def parse_glowroot_trace(raw: str) -> tuple[str, list[str]]:
    raise NotImplementedError


def generate_explain_sql(sql: str, params: list[str], options: dict) -> str:
    raise NotImplementedError
