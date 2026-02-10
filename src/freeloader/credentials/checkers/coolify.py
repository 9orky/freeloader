import httpx

from freeloader.credentials.checkers import CredentialStatus, register


@register
class CoolifyChecker:
    @property
    def name(self) -> str:
        return "coolify"

    def check_credentials(self, secrets: dict[str, str], api_url: str) -> CredentialStatus:
        token = secrets.get("COOLIFY_TOKEN", "")
        base = api_url.rstrip("/") if api_url else "https://app.coolify.io"
        resp = httpx.get(
            f"{base}/api/v1/version",
            headers={"Authorization": f"Bearer {token}",
                     "Accept": "application/json"},
            timeout=10.0,
        )
        if resp.status_code == 200:
            return CredentialStatus(valid=True, identity=f"Coolify {resp.text.strip()}")
        return CredentialStatus(valid=False, error=f"HTTP {resp.status_code}: {resp.text[:120]}")
