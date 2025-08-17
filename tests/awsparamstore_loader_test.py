"""
Tests requiring calls to AWS are recorded with vcrpy

To record new tests:

- if needed, delete the './tests/cassettes/*.yaml' file(s)
- create a .env file with the following:

```
ALLOW_TEST_RECORDING=1
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_DEFAULT_REGION=us-east-2
```

In AWS, there needs to be a few parameters to collect. The past tests
were set up with the following parameter key:values:

- (String)          /foo/bar : foo.bar (string)
- (Secure String)   /foo/baz : foo.baz (secure string)
- (String List)     /foo/biz : foo,biz (string list)
- (String)          /foo/foo2/bar: "foo foo bar" (string)
- (String)          /biz/baz : biz.baz
"""

from __future__ import annotations

import os
from collections.abc import Generator
from unittest.mock import patch

import pytest
import vcr  # type: ignore

from eggviron import AWSParamStoreException
from eggviron import AWSParamStoreLoader

boto3 = pytest.importorskip("boto3")

recorder = vcr.VCR(
    cassette_library_dir="tests/cassettes",
    record_mode="once",
    filter_headers=[
        "Authorization",
        "User-Agent",
        "X-Amz-Date",
        "X-Amz-Target",
    ],
    match_on=[
        "method",
        "body",
        "url",
    ],
)


@pytest.fixture(autouse=True)
def mock_environ() -> Generator[None, None, None]:
    """Setup mock AWS variables unless recording is being done."""
    mocked_env = {
        "AWS_ACCESS_KEY_ID": "mock",
        "AWS_SECRET_ACCESS_KEY": "mock",
        "AWS_DEFAULT_REGION": "us-east-2",
    }
    clear = not bool(os.getenv("ALLOW_TEST_RECORDING"))
    with patch.dict(os.environ, mocked_env if clear else {}, clear=clear):
        yield None


def test_init_with_boto3() -> None:
    """Test valid inputs. No results expected."""
    AWSParamStoreLoader(parameter_name="/foo/bar")
    AWSParamStoreLoader(parameter_path="/foo/bar/")


def test_init_with_incorrect_parameter_path_raises() -> None:
    """Raise a ValueError if the parameter path doesn't end with /"""
    pattern = "Given parameter path '.+' but it looks like a parameter name"

    with pytest.raises(ValueError, match=pattern):
        AWSParamStoreLoader(parameter_path="/foo/bar")


def test_init_with_incorrect_parameter_name_raises() -> None:
    """Raise a ValueError if the parameter name ends with a /"""
    pattern = "Given parameter name '.+' but it looks like a parameter path"

    with pytest.raises(ValueError, match=pattern):
        AWSParamStoreLoader(parameter_name="/foo/bar/")


def test_init_with_invalid_parameter_raises() -> None:
    """Raise a ValueError if the parameter does not start with '/'"""
    pattern = "The given parameter '.+' must start with"

    with pytest.raises(ValueError, match=pattern):
        AWSParamStoreLoader(parameter_name="foo/bar/")


def test_init_without_path_or_name_raises() -> None:
    """One of the two values are required."""
    pattern = "A valid parameter name or path is required"

    with pytest.raises(ValueError, match=pattern):
        AWSParamStoreLoader()  # type: ignore


def test_run_raises_without_region() -> None:
    """When the region is not defined an exception is raised."""
    os.environ.pop("AWS_DEFAULT_REGION", None)

    with pytest.raises(AWSParamStoreException):
        AWSParamStoreLoader(parameter_name="/foo/bar").run()


def test_run_raises_exception_when_name_not_found() -> None:
    """Ask for a parameter that does not exist to raise an exception"""

    with pytest.raises(AWSParamStoreException):
        AWSParamStoreLoader(parameter_name="/oo/bar").run()


@recorder.use_cassette()
def test_run_returns_parameter_by_name_without_truncation() -> None:
    """Return single value with full path as the key"""

    result = AWSParamStoreLoader(parameter_name="/foo/bar").run()

    assert result == {"/foo/bar": "foo.bar"}


@recorder.use_cassette()
def test_run_returns_parameter_by_name_with_truncation() -> None:
    """Return single value with just the final component of the path as the key"""
    clazz = AWSParamStoreLoader(parameter_name="/foo/bar", truncate_key=True)

    result = clazz.run()

    assert result == {"bar": "foo.bar"}


@recorder.use_cassette()
def test_run_returns_parameters_by_path_without_truncation() -> None:
    """Return all paramters found in the path, nonrecursively, with pagination"""
    expected = {
        "/foo/bar": "foo.bar",
        "/foo/baz": "AQICAHgabVcv70rp9mLGkzhrqCN34++39E3yG6opT3oWiUeIjQHzlmsgV5Gcanz46b8VrQzAAAAAZTBjBgkqhkiG9w0BBwagVjBUAgEAME8GCSqGSIb3DQEHATAeBglghkgBZQMEAS4wEQQMUdY1ipv5IuX83HMWAgEQgCLdD70T7esiOPM+anDBsrleqSXCQJJFB0sDOSeAd9wpVqwT",
        "/foo/biz": "foo,biz",
    }
    clazz = AWSParamStoreLoader(parameter_path="/foo/")

    with patch("eggviron._awsparamstore_loader._MAX_RESULTS", 1):
        results = clazz.run()

    assert results == expected


@recorder.use_cassette()
def test_run_returns_parameters_by_path_without_truncation_recursively() -> None:
    """Return all paramters found in the path, recursively, with pagination"""
    expected = {
        "/foo/bar": "foo.bar",
        "/foo/baz": "AQICAHgabVcv70rp9mLGkzhrqCN34++39E3yG6opT3oWiUeIjQHzlmsgV5Gcanz46b8VrQzAAAAAZTBjBgkqhkiG9w0BBwagVjBUAgEAME8GCSqGSIb3DQEHATAeBglghkgBZQMEAS4wEQQMUdY1ipv5IuX83HMWAgEQgCLdD70T7esiOPM+anDBsrleqSXCQJJFB0sDOSeAd9wpVqwT",
        "/foo/biz": "foo,biz",
        "/foo/foo2/bar": "foo foo bar",
    }
    clazz = AWSParamStoreLoader(parameter_path="/foo/", recursive=True)

    with patch("eggviron._awsparamstore_loader._MAX_RESULTS", 1):
        results = clazz.run()

    assert results == expected


@recorder.use_cassette()
def test_run_returns_parameters_by_path_within_truncation() -> None:
    """Return all paramters found in the path, nonrecursively, with pagination"""
    expected = {
        "bar": "foo.bar",
        "baz": "AQICAHgabVcv70rp9mLGkzhrqCN34++39E3yG6opT3oWiUeIjQHzlmsgV5Gcanz46b8VrQzAAAAAZTBjBgkqhkiG9w0BBwagVjBUAgEAME8GCSqGSIb3DQEHATAeBglghkgBZQMEAS4wEQQMUdY1ipv5IuX83HMWAgEQgCLdD70T7esiOPM+anDBsrleqSXCQJJFB0sDOSeAd9wpVqwT",
        "biz": "foo,biz",
    }
    clazz = AWSParamStoreLoader(parameter_path="/foo/", truncate_key=True)

    with patch("eggviron._awsparamstore_loader._MAX_RESULTS", 1):
        results = clazz.run()

    assert results == expected


def test_run_returns_parameters_by_path_raises_when_exceeds_max_pagination() -> None:
    """A safe-guard against infinite loops, raise if max pagination attempts are reached."""
    pattern = "Max pagination loop exceeded: _MAX_PAGINATION_LOOPS=0"
    clazz = AWSParamStoreLoader(parameter_path="/foo/")

    with (
        patch("eggviron._awsparamstore_loader._MAX_PAGINATION_LOOPS", 0),
        pytest.raises(AWSParamStoreException, match=pattern),
    ):
        clazz.run()
