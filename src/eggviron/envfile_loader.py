"""
Load local .env from CWD or path, if provided

Current format for the `.env` file supports strings only and is parsed in
the following order:

- Each seperate line is considered a new possible key/value set
- Each set is delimted by the first `=` found
- Leading and trailing whitespace are removed
- Matched leading/trailing single quotes or double quotes will be stripped from values (not keys).
"""

from __future__ import annotations

import logging
import re

_RE_LTQUOTES = re.compile(r"([\"'])(.*)\1$|^(.*)$")
_EXPORT_PREFIX = re.compile(r"^\s*?export\s")
_VALIDATE_KEY = re.compile(r"^[^\s]+$")


class EnvFileLoader:
    """Load local .env file"""

    log = logging.getLogger(__name__)
    name = "EnvFileLoader"

    def __init__(self, filename: str = "./.env") -> None:
        """
        Load local .env file.

        Args:
            filename: Filename (with path) to load, default is `./.env`
        """
        self._filename = filename

    def run(self) -> dict[str, str]:
        """Load key:pair values of file given at instantiated."""
        loaded_values = self._load_values()

        for key, value in loaded_values.items():
            self.log.debug("Found, %s : ***%s", key, value[-(len(value) // 4) :])

        return loaded_values

    def _load_values(self) -> dict[str, str]:
        """
        Load values from .env, or provided filename, to class state.

        Args:
            filename : [str] Alternate filename to load over `.env`

        Raises
            FileNotFoundError: When file cannot be found
            OSError: On file access error
        """
        self.log.debug("Reading vars from '%s'", self._filename)
        with open(self._filename, encoding="utf-8") as input_file:
            return self.parse_env_file(input_file.read())

    def parse_env_file(self, input_file: str) -> dict[str, str]:
        """Parses env file into key-pair values"""
        loaded_values = {}
        for idx, line in enumerate(input_file.split("\n"), start=1):
            if not line or line.strip().startswith("#"):
                continue

            if len(line.split("=", 1)) != 2:
                raise ValueError(f"Line {idx}: Invalid format, expecting '='")

            key, value = line.split("=", 1)

            key = _strip_export(key).strip()
            if not _is_valid_key(key):
                raise ValueError(f"Line {idx}: Invalid key, '{key}'")

            value = value.strip()

            value = _remove_lt_quotes(value)

            loaded_values[key] = value

        return loaded_values


def _remove_lt_quotes(in_: str) -> str:
    """Removes matched leading and trailing single / double quotes"""
    m = _RE_LTQUOTES.match(in_)
    return m.group(2) if m and m.group(2) else in_


def _strip_export(in_: str) -> str:
    """Removes leading 'export ' prefix"""
    return re.sub(_EXPORT_PREFIX, "", in_)


def _is_valid_key(in_: str) -> bool:
    """True if the key is value."""
    return bool(_VALIDATE_KEY.match(in_))
