import pytest
from pathlib import Path
from glowroot_parser import parse_glowroot_trace, generate_explain_sql, ParseError

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
