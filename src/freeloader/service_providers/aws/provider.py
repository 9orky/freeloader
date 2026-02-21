from ..base import ServiceProvider, Credentials
from ..registry import providers


@providers.register("aws")
class AWS(ServiceProvider):
    @property
    def name(self) -> str:
        return "aws"

    @property
    def credential_keys(self) -> list[str]:
        return ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"]

    def check_credentials(self, credentials: Credentials) -> None:
        # install boto3
        pass
