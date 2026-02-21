from ..base import ServiceProvider, Credentials
from ..registry import providers


@providers.register("git")
class Git(ServiceProvider):
    @property
    def name(self) -> str:
        return "git"

    @property
    def credential_keys(self) -> list[str]:
        return []

    def check_credentials(self, credentials: Credentials):
        pass
