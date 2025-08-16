"""
Load parameter store values from an AWS Parameter Store (SSM)

- Load a single target parameter
- Load all matching parameters from a path
"""

from __future__ import annotations

import dataclasses
import logging
from typing import overload
from typing import TYPE_CHECKING

try:
    import boto3
    from botocore.exceptions import BotoCoreError
    from botocore.exceptions import ClientError

except ImportError as err:  # pragma: no cover
    error_msg = "boto3 not installed. Install the 'aws' extra to use AWSParamStore."
    raise ImportError(error_msg) from err

if TYPE_CHECKING:
    from types_boto3_ssm import SSMClient


@dataclasses.dataclass(slots=True)
class AWSParamStoreException(Exception):
    """Exception raised by AWSParamStore."""

    message: str
    code: str | None = None
    request_id: str | None = None
    http_status_code: int | None = None
    http_headers: dict[str, str] = dataclasses.field(default_factory=dict)
    retry_attempts: int | None = None

    @classmethod
    def from_clienterror(cls, err: ClientError) -> AWSParamStoreException:
        return cls(
            message=err.response["Error"]["Message"],
            code=err.response["Error"]["Code"],
            request_id=err.response["ResponseMetadata"]["RequestId"],
            http_status_code=err.response["ResponseMetadata"]["HTTPStatusCode"],
            http_headers=err.response["ResponseMetadata"]["HTTPHeaders"],
            retry_attempts=err.response["ResponseMetadata"]["RetryAttempts"],
        )


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
        truncate_key: bool = False,
    ) -> None:
        """
        Load all key:pair values found under given path from AWS Parameter Store (SSM)

        Requires AWS access keys to be set in the environment variables.

        Args:
            parameter_path: Path of parameters. e.g.: /Finance/Prod/IAD/WinServ2016/
            aws_region: Region to load from. Defaults to AWS_REGION environment variable
            truncate_key: When True only the final component of the path will be used as the key
        """
        pass

    @overload
    def __init__(
        self,
        *,
        parameter_name: str,
        aws_region: str | None = None,
        truncate_key: bool = False,
    ) -> None:
        """
        Load a single key:pair value found under given name from AWS Parameter Store (SSM)

        Requires AWS access keys to be set in the environment variables.

        Args:
            parameter_name: Parameter name to load. e.g.: /Finance/Prod/IAD/WinServ2016/license33
            aws_region: Region to load from. Defaults to AWS_REGION environment variable
            truncate_key: When True only the final component of the name will be used as the key
        """
        pass

    def __init__(
        self,
        *,
        parameter_path: str | None = None,
        parameter_name: str | None = None,
        aws_region: str | None = None,
        truncate_key: bool = False,
    ) -> None:
        self._parameter_path = parameter_path or parameter_name or ""
        self._aws_region = aws_region
        self._truncate = truncate_key

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
            client = boto3.client("ssm", region_name=self._aws_region)
            results = self._fetch_parameter(client)

        except ClientError as err:
            raise AWSParamStoreException.from_clienterror(err)

        except BotoCoreError as err:
            raise AWSParamStoreException(err.fmt)

        return {
            key.split("/")[-1] if self._truncate else key: value
            for key, value in results.items()
            if key
        }

    def _fetch_parameter(self, client: SSMClient) -> dict[str, str]:
        """Fetch single parameter from store."""
        result = client.get_parameter(Name=self._parameter_path)

        return {result["Parameter"]["Name"]: result["Parameter"]["Value"]}
