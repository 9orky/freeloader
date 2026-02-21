from ..base import ServiceProvider, Credentials
from ..registry import providers


@providers.register("gitlab")
class GitLab(ServiceProvider):
    @property
    def name(self) -> str:
        return "gitlab"

    @property
    def credential_keys(self) -> list[str]:
        return ["GITLAB_TOKEN"]

    def check_credentials(self, credentials: Credentials) -> None:
        # install python-gitlab
        pass
