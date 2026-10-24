from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import pytest

from eggviron import AWSParamStoreException
from eggviron import AWSParamStoreLoader

# from moto import mock_aws


boto3 = pytest.importorskip("boto3")
mock_aws = pytest.importorskip("moto.mock_aws")

_DEFAULT_REGION = "us-east-2"


@pytest.fixture(autouse=True)
def isolate_aws_environment(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Isolate the tests from any environment variables set

    This also attempts to prevent boto3 from finding any local AWS creds or
    configurations to further isolate the tests.
    """
    known_aws_variables = {
        "AWS_ACCES_KEY": "testing",
        "AWS_SECRET_ACCESS_KEY": "testing",
        "AWS_SECURITY_TOKEN": "testing",
        "AWS_SESSION_TOKEN": "testing",
        "AWS_DEFAULT_REGION": _DEFAULT_REGION,
        "AWS_PROFILE": None,
    }

    for name, value in known_aws_variables.items():
        if value is not None:
            monkeypatch.setenv(name, value)
        else:
            monkeypatch.delenv(name, raising=False)

    aws_cred_file = tmp_path / "credentials"
    aws_cred_file.write_text("")
    aws_config_file = tmp_path / "config"
    aws_config_file.write_text("")
    monkeypatch.setenv("AWS_SHARED_CREDENTIALS_FILE", str(aws_cred_file))
    monkeypatch.setenv("AWS_CONFIG_FILE", str(aws_config_file))


@pytest.fixture
def build_moto_ssm() -> Generator[None, None, None]:
    """Build a mock SSM for moto to use in tests.

    The tests are set up with the following parameter key:values:

    - (String)          /foo/bar : foo.bar
    - (Secure String)   /foo/baz : foo.baz
    - (String List)     /foo/biz : foo,biz
    - (String)          /foo/foo2/bar: "foo foo bar"
    - (String)          /biz/baz : biz.baz

    """
    with mock_aws():
        client = boto3.client("ssm", _DEFAULT_REGION)

        client.put_parameter(
            Name="/foo/bar",
            Value="foo.bar",
            Type="String",
        )
        client.put_parameter(
            Name="/foo/baz",
            Value="foo.baz",
            Type="SecureString",
        )
        client.put_parameter(
            Name="/foo/biz",
            Value="foo,biz",
            Type="StringList",
        )
        client.put_parameter(
            Name="/foo/foo2/bar",
            Value="foo foo bar",
            Type="String",
        )
        client.put_parameter(
            Name="/biz/baz",
            Value="biz.baz",
            Type="String",
        )

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


@pytest.mark.usefixtures("build_moto_ssm")
def test_run_returns_parameter_by_name_without_truncation() -> None:
    """Return single value with full path as the key"""

    result = AWSParamStoreLoader(parameter_name="/foo/bar").run()

    assert result == {"/foo/bar": "foo.bar"}


@pytest.mark.usefixtures("build_moto_ssm")
def test_run_returns_parameter_by_name_with_truncation() -> None:
    """Return single value with just the final component of the path as the key"""
    clazz = AWSParamStoreLoader(parameter_name="/foo/bar", truncate_key=True)

    result = clazz.run()

    assert result == {"bar": "foo.bar"}


@pytest.mark.usefixtures("build_moto_ssm")
def test_run_returns_parameters_by_path_without_truncation() -> None:
    """Return all paramters found in the path, nonrecursively, with pagination"""
    expected = {
        "/foo/bar": "foo.bar",
        "/foo/baz": "kms:alias/aws/ssm:foo.baz",
        "/foo/biz": "foo,biz",
    }
    clazz = AWSParamStoreLoader(parameter_path="/foo/")

    with patch("eggviron._awsparamstore_loader._MAX_RESULTS", 1):
        results = clazz.run()

    assert results == expected


@pytest.mark.usefixtures("build_moto_ssm")
def test_run_returns_parameters_by_path_without_truncation_recursively() -> None:
    """Return all paramters found in the path, recursively, with pagination"""
    expected = {
        "/foo/bar": "foo.bar",
        "/foo/baz": "kms:alias/aws/ssm:foo.baz",
        "/foo/biz": "foo,biz",
        "/foo/foo2/bar": "foo foo bar",
    }
    clazz = AWSParamStoreLoader(parameter_path="/foo/", recursive=True)

    with patch("eggviron._awsparamstore_loader._MAX_RESULTS", 1):
        results = clazz.run()

    assert results == expected


@pytest.mark.usefixtures("build_moto_ssm")
def test_run_returns_parameters_by_path_within_truncation() -> None:
    """Return all paramters found in the path, nonrecursively, with pagination"""
    expected = {
        "bar": "foo.bar",
        "baz": "kms:alias/aws/ssm:foo.baz",
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
