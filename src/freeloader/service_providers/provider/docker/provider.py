import shutil

from ..auth import ServiceProvider, Credentials, ServiceProviderError
from ..registry import providers


@providers.register("docker")
class Docker(ServiceProvider):
    requires_tech_stack = True

    def check_credentials(self, credentials: Credentials) -> None:
        pass

    def check_installation(self) -> None:
        if not shutil.which("docker"):
            raise ServiceProviderError(
                "Docker is not installed / running or not found in PATH")
