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

VALID_ENV_FILE = r"""
simple=value
formated = value
        whitespace              =               value
        quoted_whitespace       = "    value    "
double_qouted = "Some qouted value"
single_qouted = 'Some qouted value'
double_nested_qouted = "'Some qouted value'"
single_nested_qouted = '"Some qouted value"'
# commented = line


leading_broken_double_nested_qouted = 'Some qouted value'"
leading_broken_single_nested_qouted = "Some qouted value"'
trailing_broken_double_nested_qouted = "'Some qouted value'
trailing_broken_single_nested_qouted = '"Some qouted value"
export export_example = elpmaxe
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


@pytest.fixture
def loader() -> Generator[EnvFileLoader, None, None]:
    """Create a loader class with a valid .env file loaded."""
    with create_file(VALID_ENV_FILE) as file_path:
        yield EnvFileLoader(file_path)


def test_missing_equals_raises_value_error() -> None:
    # Use a comment line missing the # to assert this failure catch
    contents = "FOO=BAR\nThis is comment but it doesn't start with a #"
    with create_file(contents) as file_path:
        loader = EnvFileLoader(file_path)

        with pytest.raises(ValueError, match="Line 2: Invalid format, expecting '='"):
            loader.run()


def test_space_in_key_raises_value_error() -> None:
    # Use a comment line missing the # to assert this failure catch
    contents = "FOO BAR=BAZ"
    with create_file(contents) as file_path:
        loader = EnvFileLoader(file_path)

        with pytest.raises(ValueError, match="Line 1: Invalid key, 'FOO BAR'"):
            loader.run()


def test_export_lines_are_valid(loader: EnvFileLoader) -> None:
    # Ensure lines prefixed with "export" are valid (the "export" is dropped)
    results = loader.run()

    assert results["export_example"] == "elpmaxe"


def test_whitespace_is_ignored_unless_quoted(loader: EnvFileLoader) -> None:
    # Whitespace should be trimmed unless the values are quoted
    results = loader.run()

    assert results["whitespace"] == "value"
    assert results["quoted_whitespace"] == "    value    "
