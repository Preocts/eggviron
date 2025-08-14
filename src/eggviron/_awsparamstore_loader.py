"""
Load parameter store values from an AWS Parameter Store (SSM)

- Load a single target parameter
- Load all matching parameters from a path
"""

from __future__ import annotations

import logging
from typing import overload
class AWSParamStore:
    """Load parameter store value(s) from AWS Parameter Store (SSM)."""

    log = logging.getLogger(__name__)
    name = "AWSParamStore"

    @overload
    def __init__(
        self,
        *,
        parameter_path: str,
        aws_region: str | None = None,
    ) -> None:
        """
        Load all key:pair values found under given path from AWS Parameter Store (SSM)

        Requires AWS access keys to be set in the environment variables.

        Args:
            parameter_path: Path of parameters. e.g.: /Finance/Prod/IAD/WinServ2016/
            aws_region: Region to load from. Defaults to AWS_REGION environment variable
        """
        pass

    @overload
    def __init__(
        self,
        *,
        parameter_name: str,
        aws_region: str | None = None,
    ) -> None:
        """
        Load a single key:pair value found under given name from AWS Parameter Store (SSM)

        Requires AWS access keys to be set in the environment variables.

        Args:
            parameter_name: Parameter name to load. e.g.: /Finance/Prod/IAD/WinServ2016/license33
            aws_region: Region to load from. Defaults to AWS_REGION environment variable
        """
        pass

    def __init__(
        self,
        *,
        parameter_path: str | None = None,
        parameter_name: str | None = None,
        aws_region: str | None = None,
    ) -> None:
        self._parameter_path = parameter_path
        self._parameter_name = parameter_name
        self._aws_region = aws_region

        error_msg = ""

        if not self._parameter_path and not self._parameter_name:
            error_msg = "A valid parameter name or path is required."

        elif self._parameter_path and not self._parameter_path.endswith("/"):
            error_msg = f"Given parameter path '{self._parameter_path}' but it looks like a parameter name. Did you forget and trailing '/'?"

        elif self._parameter_name and self._parameter_name.endswith("/"):
            error_msg = f"Given parameter name '{self._parameter_name}' but it looks like a parameter path. Remove the trailing '/'"

        if error_msg:
            raise ValueError(error_msg)

