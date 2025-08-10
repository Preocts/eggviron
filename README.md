[![Python 3.10 | 3.11 | 3.12 | 3.13 | 3.14](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue)](https://www.python.org/downloads)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Nox](https://img.shields.io/badge/%F0%9F%A6%8A-Nox-D85E00.svg)](https://github.com/wntrblm/nox)

[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/Preocts/eggviron/main.svg)](https://results.pre-commit.ci/latest/github/Preocts/eggviron/main)
[![Python tests](https://github.com/Preocts/eggviron/actions/workflows/python-tests.yml/badge.svg?branch=main)](https://github.com/Preocts/eggviron/actions/workflows/python-tests.yml)

# eggviron

- [Contributing Guide and Developer Setup Guide](./CONTRIBUTING.md)
- [License: MIT](./LICENSE)

---

Load tokens, secrets, and other values at run-time.

---

## `.env` file format

`.env` file is parsed with the following rules:

- Lines beginning with `#` are considered comments and ignored
- Each seperate line is considered a new possible key/value set
- Each set is delimted by the first `=` found
- Leading `export` keyword is removed from key, case agnostic
- Leading and trailing whitespace are removed
- Matched leading/trailing single quotes or double quotes will be stripped from
  values (not keys).

I'm open to suggestions on standards to follow here. This is compiled from
"crowd standard" and what is useful at the time.

This `.env` example:

```conf
# Example .env file
export PASSWORD     = correct horse battery staple
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
