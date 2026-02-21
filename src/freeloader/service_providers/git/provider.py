import shutil

from ..base import ServiceProvider, Credentials, ServiceProviderError
from ..registry import providers


@providers.register("git")
class Git(ServiceProvider):
    auth_keys = []
    requires_auth = False

    def check_credentials(self, credentials: Credentials) -> None:
        pass

    def check_installation(self) -> None:
        if not shutil.which("git"):
            raise ServiceProviderError("Git is not installed or not found in PATH")
