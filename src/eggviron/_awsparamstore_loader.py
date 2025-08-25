"""
Load parameter store values from an AWS Parameter Store (SSM)

- Load a single target parameter
- Load all matching parameters from a path
"""

from __future__ import annotations

import dataclasses
from typing import TYPE_CHECKING
from typing import overload

try:
    import boto3
    from botocore.exceptions import BotoCoreError
    from botocore.exceptions import ClientError

    _BOTO = True

except ImportError:
    _BOTO = False

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


_MAX_PAGINATION_LOOPS = 100
_MAX_RESULTS = 10


class AWSParamStoreLoader:
    """Load parameter store value(s) from AWS Parameter Store (SSM)."""

    name = "AWSParamStore"

    @overload
    def __init__(
        self,
        *,
        parameter_path: str,
        aws_region: str | None = None,
        truncate_key: bool = False,
        recursive: bool = False,
    ) -> None:
        """
        Load all key:value pairs found under given path from AWS Parameter Store (SSM)

        Requires AWS access keys to be set in the environment variables.

        Args:
            parameter_path: Path of parameters. e.g.: /Finance/Prod/IAD/WinServ2016/
            aws_region: Region to load from. Defaults to AWS_DEFAULT_REGION environment variable
            truncate_key: When True only the final component of the path will be used as the key
            recursive: Recursively load all nested paths under given path
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
        Load a single key:value pair found under given name from AWS Parameter Store (SSM)

        Requires AWS access keys to be set in the environment variables.

        Args:
            parameter_name: Parameter name to load. e.g.: /Finance/Prod/IAD/WinServ2016/license33
            aws_region: Region to load from. Defaults to AWS_DEFAULT_REGION environment variable
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
        recursive: bool = False,
    ) -> None:
        self._parameter_path = parameter_path or parameter_name or ""
        self._aws_region = aws_region
        self._truncate = truncate_key
        self._recursive = recursive

        if not _BOTO:
            error_msg = "boto3 not installed. Install the 'aws' extra to use AWSParamStore."
            raise AWSParamStoreException(error_msg)

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

            if self._parameter_path.endswith("/"):
                results = self._fetch_parameters(client)
            else:
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

    def _fetch_parameters(self, client: SSMClient) -> dict[str, str]:
        next_token = ""
        values: dict[str, str] = {}

        for _ in range(_MAX_PAGINATION_LOOPS):
            results = client.get_parameters_by_path(
                Path=self._parameter_path,
                Recursive=self._recursive,
                MaxResults=_MAX_RESULTS,
                NextToken=next_token,
            )

            for parameter in results["Parameters"]:
                values[parameter["Name"]] = parameter["Value"]

            next_token = results.get("NextToken") or ""
            if not next_token:
                break

        else:
            raise AWSParamStoreException(f"Max pagination loop exceeded: {_MAX_PAGINATION_LOOPS=}")

        return values
