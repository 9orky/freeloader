from coolipy import Coolipy, exceptions

from ..base import ServiceProvider, Credentials, ServiceProviderAuthError
from ..obtain import Info, Input, OpenURL
from ..registry import providers


@providers.register("coolify")
class Coolify(ServiceProvider):
    auth_keys = ["COOLIFY_TOKEN", "COOLIFY_ENDPOINT"]
    requires_auth = True
    obtain_token_steps = [
        Input("COOLIFY_ENDPOINT"),
        Info("Generate an API token from your Coolify dashboard."),
        OpenURL("{COOLIFY_ENDPOINT}/settings/api-tokens"),
    ]

    def check_credentials(self, credentials: Credentials) -> None:
        coolify = Coolipy(
            coolify_api_key=credentials.kv["COOLIFY_TOKEN"],
            coolify_endpoint=credentials.kv["COOLIFY_ENDPOINT"]
        )

        try:
            coolify.healthcheck()
        except exceptions.CoolipyAPIServiceException as e:
            raise ServiceProviderAuthError(str(e))
