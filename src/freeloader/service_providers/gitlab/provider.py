from gitlab import Gitlab, GitlabAuthenticationError

from ..base import ServiceProvider, Credentials, ServiceProviderAuthError
from ..registry import providers


@providers.register("gitlab")
class GitLab(ServiceProvider):
    auth_keys = ["GITLAB_TOKEN"]
    requires_auth = True

    def check_credentials(self, credentials: Credentials) -> None:
        try:
            Gitlab(private_token=credentials.kv["GITLAB_TOKEN"]).auth()
        except GitlabAuthenticationError as e:
            raise ServiceProviderAuthError(str(e))
