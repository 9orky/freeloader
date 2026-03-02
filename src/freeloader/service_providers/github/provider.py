from github import Github, BadCredentialsException, Auth

from ..base import ServiceProvider, Credentials, ServiceProviderAuthError
from ..obtain import Info, OpenURL
from ..registry import providers


@providers.register("github")
class GitHub(ServiceProvider):
    auth_keys = ["GITHUB_TOKEN"]
    requires_auth = True
    obtain_token_steps = [
        Info("Create a Personal Access Token with repo scope."),
        OpenURL("https://github.com/settings/tokens/new"),
    ]

    def check_credentials(self, credentials: Credentials) -> None:
        auth = Auth.Token(credentials.kv["GITHUB_TOKEN"])
        gh = Github(auth=auth)

        try:
            gh.get_user()
        except BadCredentialsException as e:
            raise ServiceProviderAuthError(str(e))
