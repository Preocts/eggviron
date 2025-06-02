from __future__ import annotations

import contextlib
import os
import tempfile
from collections.abc import Generator

import pytest

from eggviron.envfile_loader import EnvFileLoader

INVALID_ENV_FILE = """\
FOO=BAR
This is comment but it doesn't start with a #
"""


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


def test_invalid_format_raises_value_error() -> None:
    # Use a comment line missing the # to assert this failure catch
    with create_file(INVALID_ENV_FILE) as file_path:
        loader = EnvFileLoader(file_path)

        with pytest.raises(ValueError, match="Line 2: Invalid format, expecting '='"):
            loader.run()
