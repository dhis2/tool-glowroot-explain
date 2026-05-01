class ParseError(ValueError):
    pass


def parse_glowroot_trace(raw: str) -> tuple[str, list[str]]:
    raise NotImplementedError


def generate_explain_sql(sql: str, params: list[str], options: dict) -> str:
    raise NotImplementedError
