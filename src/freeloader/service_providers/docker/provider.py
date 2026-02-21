from ..base import ServiceProvider, Credentials
from ..registry import providers


@providers.register("docker")
class Docker(ServiceProvider):
    @property
    def name(self) -> str:
        return "docker"

    @property
    def credential_keys(self) -> list[str]:
        return []

    def check_credentials(self, credentials: Credentials):
        pass

    def requires_tech_stack(self) -> bool:
        return True
