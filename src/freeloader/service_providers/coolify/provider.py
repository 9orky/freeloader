from ..base import ServiceProvider, Credentials
from ..registry import providers


@providers.register("coolify")
class Coolify(ServiceProvider):
    @property
    def name(self) -> str:
        return "coolify"

    @property
    def credential_keys(self) -> list[str]:
        return ["COOLIFY_TOKEN", "COOLIFY_URL"]

    def check_credentials(self, credentials: Credentials) -> None:
        # install coolipy
        pass