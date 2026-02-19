import httpx

from freeloader.secrets import register
from ..base import ServiceProvider, Credentials

_API_URL = "https://app.coolify.io"

@register
class CoolifyChecker(ServiceProvider):
    @property
    def name(self) -> str:
        return "coolify"

    @property
    def credential_keys(self) -> list[str]:
        return ["COOLIFY_TOKEN"]

    def check_credentials(self, credentials: Credentials) -> None:
        token = credentials.kv.get("COOLIFY_TOKEN", "")
        base = _API_URL
        resp = httpx.get(
            f"{base}/api/v1/version",
            headers={"Authorization": f"Bearer {token}",
                     "Accept": "application/json"},
            timeout=10.0,
        )
    
        if resp.status_code != 200:
            raise ValueError("Invalid credentials")
