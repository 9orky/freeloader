import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from ..base import ServiceProvider, Credentials, ServiceProviderAuthError
from ..obtain import OpenURL
from ..registry import providers


@providers.register("aws")
class AWS(ServiceProvider):
    auth_keys = ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"]
    requires_auth = True
    obtain_token_steps = [
        OpenURL("https://console.aws.amazon.com/iam/home#/security_credentials"),
    ]

    def check_credentials(self, credentials: Credentials) -> None:
        session = boto3.Session(
            aws_access_key_id=credentials.kv["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=credentials.kv["AWS_SECRET_ACCESS_KEY"],
            region_name=credentials.kv.get("AWS_REGION", "eu-central-1"),
        )

        try:
            sts = session.client('sts')
            sts.get_caller_identity()
        except (ClientError, NoCredentialsError) as e:
            raise ServiceProviderAuthError(str(e))
