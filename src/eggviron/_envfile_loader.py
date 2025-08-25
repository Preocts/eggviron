"""
Load local .env from CWD or path, if provided

`.env` file is parsed with the following rules:

- Lines beginning with `#` are considered comments and ignored
- Each seperate line is considered a new possible key/value set
- Each set is delimted by the first `=` found
- Leading `export` keyword is removed from key, case agnostic
- Leading and trailing whitespace are removed
- Matched leading/trailing single quotes or double quotes will be stripped from values (not keys).

This `.env` example:

```conf
# Example .env file
export PASSWORD     = correct horse battery staple  # great password
USER_NAME           = "not_admin"
MESSAGE             = '    Totally not an "admin" account logging in'
```

Will be parsed as:

```python
{
    "PASSWORD": "correct horse battery staple",
    "USER_NAME": "not_admin",
    "MESSAGE": '    Totally not an "admin" account logging in',
}
```

"""

from __future__ import annotations

import re

_RE_LTQUOTES = re.compile(r"^\s*?([\"'])(.*)\1(\s+[#;].*)?$")
_EXPORT_PREFIX = re.compile(r"^\s*?export\s")
_INLINE_COMMENT = re.compile(r"^(.+)(\s+[#;].*)$")
_COMMENT_CHARS = ["#", ";"]


class EnvFileLoader:
    """Load local .env file"""

    name = "EnvFileLoader"

    def __init__(self, filename: str = "./.env") -> None:
        """
        Load local .env file.

        Args:
            filename: Filename (with path) to load, default is `./.env`
        """
        self._filename = filename

    def run(self) -> dict[str, str]:
        """
        Load key:value pairs of file given at instantiated.

        Args:
            filename : [str] Alternate filename to load over `.env`

        Raises
            FileNotFoundError: When file cannot be found
            OSError: On file access error
        """
        with open(self._filename, encoding="utf-8") as input_file:
            return self.parse_env_file(input_file.read())

    def parse_env_file(self, input_file: str) -> dict[str, str]:
        """Parses env file into key-pair values"""
        loaded_values = {}
        for idx, line in enumerate(input_file.split("\n"), start=1):
            if not line or line.strip()[0] in _COMMENT_CHARS:
                continue

            if len(line.split("=", 1)) != 2:
                raise ValueError(f"Line {idx}: Invalid format, expecting '='")

            key, value = line.split("=", 1)

            key = _strip_export(key).strip()

            value, was_quoted = _remove_lt_quotes(value)

            if not was_quoted:
                value = _remove_inline_comment(value)

            loaded_values[key] = value if was_quoted else value.strip()

        return loaded_values


def _remove_lt_quotes(in_: str) -> tuple[str, bool]:
    """Removes matched leading and trailing single / double quotes"""
    m = _RE_LTQUOTES.match(in_)
    return m.group(2) if m and m.group(2) else in_, bool(m and m.group(2))


def _strip_export(in_: str) -> str:
    """Removes leading 'export ' prefix"""
    return re.sub(_EXPORT_PREFIX, "", in_)


def _remove_inline_comment(in_: str) -> str:
    """Remove inline comments."""
    m = _INLINE_COMMENT.match(in_)
    return m.group(1) if m else in_
