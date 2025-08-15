"""
Load parameter store values from an AWS Parameter Store (SSM)

- Load a single target parameter
- Load all matching parameters from a path
"""

from __future__ import annotations

import dataclasses
import logging
from typing import overload


@dataclasses.dataclass(slots=True)
class AWSParamStoreException(Exception):
    """Exception raised by AWSParamStore."""

    message: str
    code: str | None = None
    request_id: str | None = None
    host_id: str | None = None
    http_status_code: int | None = None
    http_headers: dict[str, str] = dataclasses.field(default_factory=dict)
    retry_attempts: int | None = None

    @classmethod
    def from_clienterror(cls, err: ClientError) -> AWSParamStoreException:
        return cls(
            message=err.response["Error"]["Message"],
            code=err.response["Error"]["Code"],
            request_id=err.response["ResponseMetadata"]["RequestId"],
            host_id=err.response["ResponseMetadata"]["HostId"],
            http_status_code=err.response["ResponseMetadata"]["HTTPStatusCode"],
            http_headers=err.response["ResponseMetadata"]["HTTPHeaders"],
            retry_attempts=err.response["ResponseMetadata"]["RetryAttempts"],
        )


try:
    import boto3
    from botocore.exceptions import BotoCoreError
    from botocore.exceptions import ClientError

except ImportError:
    error_msg = "boto3 not installed. Install the 'aws' extra to use AWSParamStore."
    raise AWSParamStoreException(error_msg)


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
        self._parameter_path = parameter_path or parameter_name
        self._aws_region = aws_region

        error_msg = ""

        if not parameter_path and not parameter_name:
            error_msg = "A valid parameter name or path is required."

        elif parameter_path and not parameter_path.endswith("/"):
            error_msg = f"Given parameter path '{parameter_path}' but it looks like a parameter name. Did you forget the trailing '/'?"

        elif parameter_name and parameter_name.endswith("/"):
            error_msg = f"Given parameter name '{parameter_name}' but it looks like a parameter path. Remove the trailing '/'."

        if self._parameter_path and not self._parameter_path.startswith("/"):
            error_msg = f"Invalid parameter: The given parameter '{self._parameter_path}' must start with a '/' to be valid."

        if error_msg:
            raise ValueError(error_msg)

    def run(self) -> dict[str, str]:
        """Fetch values from AWS Parameter store."""
        try:
            boto3.client("ssm", region_name=self._aws_region)

        except ClientError as err:
            raise AWSParamStoreException.from_clienterror(err)
        except BotoCoreError as err:
            raise AWSParamStoreException(err.fmt)

        return {}
