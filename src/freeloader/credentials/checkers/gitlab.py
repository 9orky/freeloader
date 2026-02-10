import httpx

from freeloader.credentials.checkers import CredentialStatus, register


@register
class GitLabChecker:
    @property
    def name(self) -> str:
        return "gitlab"

    def check_credentials(self, secrets: dict[str, str], api_url: str) -> CredentialStatus:
        token = secrets.get("GITLAB_TOKEN", "")
        resp = httpx.get(
            "https://gitlab.com/api/v4/user",
            headers={"PRIVATE-TOKEN": token},
            timeout=10.0,
        )
        if resp.status_code == 200:
            username = resp.json().get("username", "unknown")
            return CredentialStatus(valid=True, identity=username)
        return CredentialStatus(valid=False, error=f"HTTP {resp.status_code}: {resp.text[:120]}")
