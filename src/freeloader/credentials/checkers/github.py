import httpx

from freeloader.credentials.checkers import CredentialStatus, register


@register
class GitHubChecker:
    @property
    def name(self) -> str:
        return "github"

    def check_credentials(self, secrets: dict[str, str], api_url: str) -> CredentialStatus:
        token = secrets.get("GITHUB_TOKEN", "")
        resp = httpx.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {token}",
                     "Accept": "application/json"},
            timeout=10.0,
        )
        if resp.status_code == 200:
            login = resp.json().get("login", "unknown")
            return CredentialStatus(valid=True, identity=login)
        return CredentialStatus(valid=False, error=f"HTTP {resp.status_code}: {resp.text[:120]}")
