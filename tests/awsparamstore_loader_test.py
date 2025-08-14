from __future__ import annotations

import pytest

from eggviron import AWSParamStore
from eggviron import AWSParamStoreException
from eggviron._awsparamstore_loader import _NO_BOTO3 as SKIP_BOTO


@pytest.mark.skipif(not SKIP_BOTO, reason="boto3 installed")
def test_init_without_boto3() -> None:
    pattern = "boto3 not installed. Install the 'aws' extra to use AWSParamStore."

    with pytest.raises(AWSParamStoreException, match=pattern):
        AWSParamStore(parameter_name="/foo/bar")


@pytest.mark.skipif(SKIP_BOTO, reason="boto3 not installed")
def test_init_with_boto3() -> None:
    """Test valid inputs. No results expected."""
    AWSParamStore(parameter_name="/foo/bar")
    AWSParamStore(parameter_path="/foo/bar/")


@pytest.mark.skipif(SKIP_BOTO, reason="boto3 not installed")
def test_init_with_incorrect_parameter_path_raises() -> None:
    """Raise a ValueError if the parameter path doesn't end with /"""
    pattern = "Given parameter path '.+' but it looks like a parameter name"

    with pytest.raises(ValueError, match=pattern):
        AWSParamStore(parameter_path="/foo/bar")


@pytest.mark.skipif(SKIP_BOTO, reason="boto3 not installed")
def test_init_with_incorrect_parameter_name_raises() -> None:
    """Raise a ValueError if the parameter name ends with a /"""
    pattern = "Given parameter name '.+' but it looks like a parameter path"

    with pytest.raises(ValueError, match=pattern):
        AWSParamStore(parameter_name="/foo/bar/")


@pytest.mark.skipif(SKIP_BOTO, reason="boto3 not installed")
def test_init_without_path_or_name_raises() -> None:
    """One of the two values are required."""
    pattern = "A valid parameter name or path is required"

    with pytest.raises(ValueError, match=pattern):
        AWSParamStore()  # type: ignore


@pytest.mark.skipif(SKIP_BOTO, reason="boto3 not installed")
def test_run_raises_without_region() -> None:
    """When the region is not defined an exception is raised."""

    with pytest.raises(AWSParamStoreException):
        AWSParamStore(parameter_name="/foo/bar").run()


@pytest.mark.skipif(SKIP_BOTO, reason="boto3 not installed")
def test_run_with_region() -> None:
    """WIP"""

    result = AWSParamStore(parameter_name="/foo/bar", aws_region="us-east-2").run()

    assert result == {}
