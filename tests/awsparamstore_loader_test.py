from __future__ import annotations

import pytest

from eggviron import AWSParamStore
from eggviron import AWSParamStoreException


def test_init() -> None:
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


def test_init_without_path_or_name_raises() -> None:
    """One of the two values are required."""
    pattern = "A valid parameter name or path is required"

    with pytest.raises(ValueError, match=pattern):
        AWSParamStore()  # type: ignore


def test_run_raises_without_region() -> None:
    """When the region is not defined an exception is raised."""

    with pytest.raises(AWSParamStoreException):
        AWSParamStore(parameter_name="/foo/bar").run()


def test_run_with_region() -> None:
    """WIP"""

    result = AWSParamStore(parameter_name="/foo/bar", aws_region="us-east-2").run()

    assert result == {}
