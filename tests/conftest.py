from __future__ import annotations

import os
from collections.abc import Generator
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def clear_environ() -> Generator[None, None, None]:
    """Ensure the environment variables are clean for all test runs."""
    mocked_env = {
        "AWS_ACCESS_KEY_ID": "mock",
        "AWS_SECRET_ACCESS_KEY": "mock",
        "AWS_DEFAULT_REGION": "us-east-2",
    }
    clear = not bool(os.getenv("ALLOW_TEST_RECORDING"))
    with patch.dict(os.environ, mocked_env if clear else {}, clear=clear):
        yield None
