from __future__ import annotations

import contextlib
import os
import tempfile
from collections.abc import Generator

import pytest

from eggviron._envfile_loader import EnvFileLoader

VALID_ENV_FILE = r"""
simple=value
formated = value
        whitespace              =               value
        quoted_whitespace       = "    value    "
double_quoted = "Some quoted value"
single_quoted = 'Some quoted value'
double_nested_quoted = "'Some quoted value'"
single_nested_quoted = '"Some quoted value"'
# commented = line
; This is also a comment

leading_broken_double_nested_quoted = 'Some quoted value'"
leading_broken_single_nested_quoted = "Some quoted value"'
trailing_broken_double_nested_quoted = "'Some quoted value'
trailing_broken_single_nested_quoted = '"Some quoted value"
export export_example = elpmaxe
actually valid = neat

inline=comments # Are allowed
inline_with_spaces=values have spaces ; and comments
quoted_inline="comments # are part of the quoted string"
quoted_inline_comment="comments # are part of the quoted string" ;Inline still allowed
inline_comment=weak!@#$%password1234 # Inline require whitespace
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


def test_spaces_in_keys(loader: EnvFileLoader) -> None:
    # It is valid to have a space in environment variables
    # https://pubs.opengroup.org/onlinepubs/9799919799/
    results = loader.run()

    assert results["actually valid"] == "neat"


def test_export_lines_are_valid(loader: EnvFileLoader) -> None:
    # Ensure lines prefixed with "export" are valid (the "export" is dropped)
    results = loader.run()

    assert results["export_example"] == "elpmaxe"


def test_whitespace_is_ignored_unless_quoted(loader: EnvFileLoader) -> None:
    # Whitespace should be trimmed unless the values are quoted
    results = loader.run()

    assert results["whitespace"] == "value"
    assert results["quoted_whitespace"] == "    value    "


def test_single_quotes_are_removed_around_values(loader: EnvFileLoader) -> None:
    # 'Single quotes' should be stripped from around a value.
    # Inner quotes should remain.
    results = loader.run()

    assert results["single_quoted"] == "Some quoted value"
    assert results["single_nested_quoted"] == '"Some quoted value"'


def test_double_quotes_are_removed_around_values(loader: EnvFileLoader) -> None:
    # "Double quotes" should be stripped from around a value.
    # Inner quotes should remain.
    results = loader.run()

    assert results["double_quoted"] == "Some quoted value"
    assert results["double_nested_quoted"] == "'Some quoted value'"


def test_leading_broken_double_nested_quotes(loader: EnvFileLoader) -> None:
    # If the qoute style doesn't match the first and last character of the line
    # then no characters should be stripped.
    results = loader.run()

    assert results["leading_broken_double_nested_quoted"] == "'Some quoted value'\""
    assert results["leading_broken_single_nested_quoted"] == '"Some quoted value"\''
    assert results["trailing_broken_double_nested_quoted"] == "\"'Some quoted value'"
    assert results["trailing_broken_single_nested_quoted"] == '\'"Some quoted value"'


def test_inline_comments_are_ignored(loader: EnvFileLoader) -> None:
    # If an inline comment is not quoted, ignore everything past the # character
    results = loader.run()

    assert results["inline"] == "comments"
    assert results["inline_with_spaces"] == "values have spaces"


def test_quoted_inline_comments_are_retained(loader: EnvFileLoader) -> None:
    # If an quoted string has a # in it, the full quoted string is still returned
    results = loader.run()

    assert results["quoted_inline"] == "comments # are part of the quoted string"
    assert results["quoted_inline_comment"] == "comments # are part of the quoted string"


def test_inline_comments_require_whitespace(loader: EnvFileLoader) -> None:
    # Don't strip comments unless the # has leading whitespace
    results = loader.run()

    assert results["inline_comment"] == "weak!@#$%password1234"
