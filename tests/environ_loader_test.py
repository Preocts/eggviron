from __future__ import annotations

import os

from eggviron._environ_loader import EnvironLoader


def test_environ_loader_returns_os_environ() -> None:
    # This is a simple loader doing a simple task
    os.environ["SOME_FAKE_KEY"] = "foo"
    expected_results = dict(os.environ)

    results = EnvironLoader().run()

    assert results == expected_results
