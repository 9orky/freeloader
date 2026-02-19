import httpx

from freeloader.secret import register
from ..base import ServiceProvider, Credentials

_API_URL = "https://api.github.com"


@register
class GitHubChecker(ServiceProvider):
    @property
    def name(self) -> str:
        return "github"

    @property
    def credential_keys(self) -> list[str]:
        return ["GITHUB_TOKEN"]

    def check_credentials(self, credentials: Credentials) -> None:
        token = credentials.kv.get("GITHUB_TOKEN", "")
        resp = httpx.get(
            f"{_API_URL}/user",
            headers={"Authorization": f"Bearer {token}",
                     "Accept": "application/json"},
            timeout=10.0,
        )
        if resp.status_code != 200:
            raise ValueError(f"HTTP {resp.status_code}: {resp.text[:120]}")
