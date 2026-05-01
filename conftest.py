"""Root conftest — suppress pytest exit-5 (no tests collected) during scaffolding."""
import pytest


def pytest_sessionfinish(session, exitstatus):
    """Allow empty test runs to exit 0 while the test suite is being built."""
    if exitstatus == pytest.ExitCode.NO_TESTS_COLLECTED:
        session.exitstatus = 0
