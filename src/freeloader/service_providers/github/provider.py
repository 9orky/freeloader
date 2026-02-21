from ..base import ServiceProvider, Credentials
from ..registry import providers


@providers.register("github")
class GitHub(ServiceProvider):
    @property
    def name(self) -> str:
        return "github"

    @property
    def credential_keys(self) -> list[str]:
        return ["GITHUB_TOKEN"]

    def check_credentials(self, credentials: Credentials) -> None:
        # install PyGithub
        pass
