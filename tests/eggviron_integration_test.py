from __future__ import annotations

import contextlib
import os
import tempfile
from collections.abc import Generator

from eggviron import Eggviron
from eggviron import EnvFileLoader
from eggviron import EnvironLoader


@contextlib.contextmanager
def create_file(contents: str) -> Generator[str, None, None]:
    """Create a tempfile filled with the contents. Yields the filepath."""
    try:
        file_descriptor, file_path = tempfile.mkstemp()
        os.close(file_descriptor)

        with open(file_path, "w", encoding="utf-8") as outfile:
            outfile.write(contents)

        yield file_path

    finally:
        os.remove(file_path)


def test_integration_of_local_loaders() -> None:
    """All loaders that do not require external IO calls."""
    env_file = "from_file=file_value"
    os.environ["FROM_ENVIRON"] = "environ_value"

    with create_file(env_file) as filepath:

        environ = Eggviron().load(EnvironLoader(), EnvFileLoader(filepath))

    assert environ["from_file"] == "file_value"
    assert environ["FROM_ENVIRON"] == "environ_value"
