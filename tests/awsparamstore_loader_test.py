from __future__ import annotations

from unittest.mock import patch

import pytest

from eggviron import AWSParamStore
from eggviron import AWSParamStoreException

boto3 = pytest.importorskip("boto3")


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


def test_run_returns_parameter_by_name_without_truncation() -> None:
    """Return single value with full path as the key"""

    result = AWSParamStore(parameter_name="/foo/bar").run()

    assert result == {"/foo/bar": "foo.bar"}


def test_run_returns_parameter_by_name_with_truncation() -> None:
    """Return single value with just the final component of the path as the key"""
    clazz = AWSParamStore(parameter_name="/foo/bar", truncate_key=True)

    result = clazz.run()

    assert result == {"bar": "foo.bar"}


def test_run_raises_exception_when_name_not_found() -> None:
    """Ask for a parameter that does not exist to raise an exception"""

    with pytest.raises(AWSParamStoreException):
        AWSParamStore(parameter_name="/oo/bar").run()


def test_run_returns_parameters_by_path_without_truncation() -> None:
    """Return all paramters found in the path, nonrecursively, with pagination"""
    expected = {
        "/foo/bar": "foo.bar",
        "/foo/baz": "kms:alias/aws/ssm:foo.baz",
        "/foo/biz": "foo,biz",
    }
    clazz = AWSParamStore(parameter_path="/foo/")

    with patch("eggviron._awsparamstore_loader._MAX_RESULTS", 1):
        results = clazz.run()

    assert results == expected


def test_run_returns_parameters_by_path_without_truncation_recursively() -> None:
    """Return all paramters found in the path, recursively, with pagination"""
    expected = {
        "/foo/bar": "foo.bar",
        "/foo/baz": "kms:alias/aws/ssm:foo.baz",
        "/foo/biz": "foo,biz",
        "/foo/foo2/bar": "foo foo bar",
    }
    clazz = AWSParamStore(parameter_path="/foo/", recursive=True)

    with patch("eggviron._awsparamstore_loader._MAX_RESULTS", 1):
        results = clazz.run()

    assert results == expected


def test_run_returns_parameters_by_path_within_truncation() -> None:
    """Return all paramters found in the path, nonrecursively, with pagination"""
    expected = {
        "bar": "foo.bar",
        "baz": "kms:alias/aws/ssm:foo.baz",
        "biz": "foo,biz",
    }
    clazz = AWSParamStore(parameter_path="/foo/", truncate_key=True)

    with patch("eggviron._awsparamstore_loader._MAX_RESULTS", 1):
        results = clazz.run()

    assert results == expected


def test_run_returns_parameters_by_path_raises_when_exceeds_max_pagination() -> None:
    """A safe-guard against infinite loops, raise if max pagination attempts are reached."""
    pattern = "Max pagination loop exceeded: _MAX_PAGINATION_LOOPS=1"
    clazz = AWSParamStore(parameter_path="/foo/")

    with (
        patch("eggviron._awsparamstore_loader._MAX_RESULTS", 1),
        patch("eggviron._awsparamstore_loader._MAX_PAGINATION_LOOPS", 1),
        pytest.raises(AWSParamStoreException, match=pattern),
    ):
        clazz.run()
