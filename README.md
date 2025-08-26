[![Python 3.10 | 3.11 | 3.12 | 3.13 | 3.14](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue)](https://www.python.org/downloads)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Nox](https://img.shields.io/badge/%F0%9F%A6%8A-Nox-D85E00.svg)](https://github.com/wntrblm/nox)

[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/Preocts/eggviron/main.svg)](https://results.pre-commit.ci/latest/github/Preocts/eggviron/main)
[![Python tests](https://github.com/Preocts/eggviron/actions/workflows/python-tests.yml/badge.svg?branch=main)](https://github.com/Preocts/eggviron/actions/workflows/python-tests.yml)

# eggviron

- [Contributing Guide and Developer Setup Guide](./CONTRIBUTING.md)
- [License: MIT](./LICENSE)

---

Manage loading key:value pairs at runtime from various sources. Values can then
be accessed from `os.environ` similar to the
[`python-dotenv`](https://pypi.org/project/python-dotenv/) library.
Additionally, the `Eggviron` object provides a dictionary-like interface for
accessing all loaded values. All keys and values are stored as strings with
methods in Eggviron for converting to int, float, and bool as needed.

Eggviron is designed to fail early and fail often. This allows for failures of
environment setup to be caught quickly, removing assumption.

Don't want to mutate the `os.environ`? Turn off mutation when using the
`Eggviron` class.

Loaders allow the selection of source for the key:value pairs and which order
they are loaded in. Prevent clobbering existing values when loading multiple
sources by default.

## Install

```console
pip install eggviron
```

### Example:

```py
from eggviron import Eggviron
from eggviron import EnvFileLoader
from eggviron import AWSParamStoreLoader

environ = Eggviron().load(
    # Load the local '.env' file
    EnvFileLoader(),
    # Load all key:value pairs from AWS Parameter Store
    AWSParamStoreLoader(parameter_path="/prod/frontend-api/"),
)

print(f"Using local account: {environ['ACCOUNT_ID']}")
print(f"New UI feature flag: {environ.get_bool('FEATURE_FLAG_NEW_UI')}")
```

---

## Logging

- Logger name: `eggviron`
- No handlers, levels, or formatters are applied to the core library
- Minimal logging is used.

---

## API Reference

### Eggviron(*, raise_on_overwrite: bool = True, mutate_environ: bool = True)

A key:value store optionally loaded through Loaders. By default, key:value pairs
added

- raise_on_overwrite: If True a KeyError will be raised when an existing key is
  overwritten by an assignment or load() action.
- mutate_environ: If True then the os.environ values are mutated when .load() is
  run or Eggviron is updated.

#### load(loader: Loader) -> Eggviron

Use loader(s) to update the loaded values. Loaders are used in the order
provided. Key:value pairs are added to os.environ after each loader is run if
mutation is allow.

#### get(key: str, default: str | None = None) -> str

Get a value from the `Eggviron`. If default is None and the key is not found, a
KeyError will be raised.

#### get_int(key: str, default: int | None = None) -> int

Get a value from the `Eggviron`, converting it to an int. If default is None and
the key is not found, a KeyError will be raised.

#### get_float(key: str, default: float | None = None) -> float

Get a value from the `Eggviron`, converting it to an float. If default is None and
the key is not found, a KeyError will be raised.

#### get_bool(key: str, default: bool | None = None) -> bool

Get a value from the `Eggviron`, converting it to an bool. If default is None and
the key is not found, a KeyError will be raised.

Valid boolean values are "true", "false", "1", and "0" (case insensitive)

### EnvironLoader()

Load current `os.environ` key:value pairs into the Eggviron instance.

### EnvFileLoader(filename: str = "./.env")

Load a local '.env' file into the Eggviron instance.

### AWSParamStoreLoader (*, parameter_path: str, parameter_name: str, aws_region: str | None = None, truncate_key: bool = False, recursive: bool = False)

Load all key:value pairs found under given path from AWS Parameter Store (SSM).
Requires AWS access keys to be set in the environment variables. Only
parameter_path or parameter_name is accepted, not both.

- parameter_path: Path of parameters. e.g.: /Finance/Prod/IAD/WinServ2016/
- parameter_name: Parameter name to load. e.g.: /Finance/Prod/IAD/WinServ2016/license33
- aws_region: Region to load from. Defaults to AWS_DEFAULT_REGION environment variable
- truncate_key: When True only the final component of the path will be used as the key
- recursive: Recursively load all nested paths under given parameter_path

The `AWSParamStoreLoader` requires `boto3` and `botocore` to be installed. If
eggviron is installed with the `aws` extra, these packages will be included.

For convenience, `AWSParamStoreLoader` will raise `AWSParamStoreException` for
all `boto3` client errors with detailed attributes for troubleshooting.

### AWSParamStoreException(message: str, code: str | None, request_id: str | None, http_status_code: int | None = None, http_headers: dict[str, str] = {}, retry_attemps: int | None = None)

Raised from all `botocore.exceptions.ClientError` and
`botocore.exceptions.BotoCoreError` exceptions in `AWSParamStoreLoader`. If
available, contains the required information for troubleshooting the error.

---

## env file format

The env file format supports many formatting features.

```ini
# Comments are allowed
; With either leading charater
simple=value # Inline comments are supported
complex = value; there must be a leading whitespace for inline comments
quoted = 'First layer of matching quotes is stripped'
trickery="We're #1 but only because of the quotes here"
# leading export keywords are stripped
export TOKEN = sometoken
; Whitespace around key:pairs is trimmed except when quoted
    whitespace    =    trimmed
```

```json
{
  "simple": "value",
  "complex": "value; there must be a leading whitespace for inline comments",
  "quoted": "First layer of matching quotes is stripped",
  "trickery": "We're #1 but only because of the quotes here",
  "TOKEN": "sometoken",
  "whitespace": "trimmed"
}
```
