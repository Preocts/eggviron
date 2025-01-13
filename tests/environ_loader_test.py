from __future__ import annotations

import os

import pytest

from eggviron.environ_loader import EnvironLoader


@pytest.fixture(autouse=True)
def clear_environ() -> None:
    # Clearing the os.environ before tests will help prevent leaking any actual secrets
    # in the environment during a failure in the test run-time.
    for key in os.environ.keys():
        os.environ.pop(key)

    os.environ["SOME_FAKE_KEY"] = "foo"


def test_environ_loader_returns_os_environ() -> None:
    # This is a simple loader doing a simple task
    expected_results = dict(os.environ)

    results = EnvironLoader().run()

    assert results == expected_results
