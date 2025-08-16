from __future__ import annotations

import sys

import pytest

from eggviron import AWSParamStore
from eggviron import AWSParamStoreException


@pytest.mark.skipif("boto3" in sys.modules, reason="boto3 installed")
def test_raise_without_boto_installed() -> None:
    """Without boto, class should raise on creation"""
    pattern = "no"
    with pytest.raises(AWSParamStoreException, match=pattern):
        AWSParamStore(parameter_name="/foo")
