from coolipy import Coolipy, exceptions

from ..base import ServiceProvider, Credentials, ServiceProviderAuthError
from ..registry import providers


@providers.register("coolify")
class Coolify(ServiceProvider):
    auth_keys = ["COOLIFY_TOKEN", "COOLIFY_ENDPOINT"]
    requires_auth = True

    def check_credentials(self, credentials: Credentials) -> None:
        coolify = Coolipy(
            coolify_api_key=credentials.kv["COOLIFY_TOKEN"],
            coolify_endpoint=credentials.kv["COOLIFY_ENDPOINT"]
        )

        try:
            coolify.healthcheck()
        except exceptions.CoolipyAPIServiceException as e:
            raise ServiceProviderAuthError(str(e))
