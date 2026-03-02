from gitlab import Gitlab, GitlabAuthenticationError

from ..base import ServiceProvider, Credentials, ServiceProviderAuthError
from ..obtain import Info, OpenURL
from ..registry import providers


@providers.register("gitlab")
class GitLab(ServiceProvider):
    auth_keys = ["GITLAB_TOKEN"]
    requires_auth = True
    obtain_token_steps = [
        Info("Create a Personal Access Token with api scope."),
        OpenURL("https://gitlab.com/-/user_settings/personal_access_tokens"),
    ]

    def check_credentials(self, credentials: Credentials) -> None:
        try:
            Gitlab(private_token=credentials.kv["GITLAB_TOKEN"]).auth()
        except GitlabAuthenticationError as e:
            raise ServiceProviderAuthError(str(e))
