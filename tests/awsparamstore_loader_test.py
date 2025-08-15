from __future__ import annotations

from collections.abc import Generator

import pytest
from moto import mock_aws

from eggviron import AWSParamStore
from eggviron import AWSParamStoreException

boto3 = pytest.importorskip("boto3")

DEFAULT_REGION = "us-east-2"


@pytest.fixture
def mock_ssm() -> Generator[None, None, None]:
    """Mock the parameter store."""
    with mock_aws():
        client = boto3.client("ssm", DEFAULT_REGION)
        client.put_parameter(Name="/biz/baz", Value="foo.bar", Type="String")
        client.put_parameter(Name="/foo/bar", Value="foo.bar", Type="String")
        client.put_parameter(Name="/foo/baz", Value="foo.baz", Type="SecureString")
        client.put_parameter(Name="/foo/biz", Value="foo,bar", Type="StringList")

        yield None


def test_init_with_boto3() -> None:
    """Test valid inputs. No results expected."""
    AWSParamStore(parameter_name="/foo/bar")
    AWSParamStore(parameter_path="/foo/bar/")


def test_init_with_incorrect_parameter_path_raises() -> None:
    """Raise a ValueError if the parameter path doesn't end with /"""
    pattern = "Given parameter path '.+' but it looks like a parameter name"

    with pytest.raises(ValueError, match=pattern):
        AWSParamStore(parameter_path="/foo/bar")


def test_init_with_incorrect_parameter_name_raises() -> None:
    """Raise a ValueError if the parameter name ends with a /"""
    pattern = "Given parameter name '.+' but it looks like a parameter path"

    with pytest.raises(ValueError, match=pattern):
        AWSParamStore(parameter_name="/foo/bar/")


def test_init_with_invalid_parameter_raises() -> None:
    """Raise a ValueError if the parameter does not start with '/'"""
    pattern = "The given parameter '.+' must start with"

    with pytest.raises(ValueError, match=pattern):
        AWSParamStore(parameter_name="foo/bar/")


def test_init_without_path_or_name_raises() -> None:
    """One of the two values are required."""
    pattern = "A valid parameter name or path is required"

    with pytest.raises(ValueError, match=pattern):
        AWSParamStore()  # type: ignore


def test_run_raises_without_region() -> None:
    """When the region is not defined an exception is raised."""

    with pytest.raises(AWSParamStoreException):
        AWSParamStore(parameter_name="/foo/bar").run()


@pytest.mark.usefixtures("mock_ssm")
def test_run_with_region() -> None:
    """WIP"""

    result = AWSParamStore(parameter_name="/foo/bar", aws_region=DEFAULT_REGION).run()

    assert result == {}
