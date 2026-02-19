import httpx

from freeloader.secrets.checkers import CredentialStatus, register
from ..base import ServiceProvider, Credentials


@register
class GitLabChecker(ServiceProvider):
    @property
    def name(self) -> str:
        return "gitlab"

    @property
    def credential_keys(self) -> list[str]:
        return ["GITLAB_TOKEN"]

    def check_credentials(self, credentials: Credentials) -> None:
        token = credentials.kv.get("GITLAB_TOKEN", "")
        resp = httpx.get(
            "https://gitlab.com/api/v4/user",
            headers={"PRIVATE-TOKEN": token},
            timeout=10.0,
        )
        if resp.status_code != 200:
            raise ValueError(f"HTTP {resp.status_code}: {resp.text[:120]}")
