from __future__ import annotations

import os

import pytest


@pytest.fixture(autouse=True)
def isolate_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Isolate the tests from any environment variables set."""
    for key in os.environ:
        monkeypatch.delenv(key)
