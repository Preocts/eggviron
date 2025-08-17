from __future__ import annotations

import os
from collections.abc import Generator
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def clear_environ() -> Generator[None, None, None]:
    """Ensure the environment variables are clean for all test runs."""
    with patch.dict(os.environ, {}, clear=True):
        yield None
