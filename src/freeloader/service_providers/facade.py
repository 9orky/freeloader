from ..secrets import has_secrets

from .registry import load_all_providers, ServiceProvider, load_provider
from .base import Credentials


class ServiceProviders:
    def get_credential_keys(self, name: str) -> list[str]:
        provider = load_provider(name)
        return provider.credential_keys

    def authorize_provider(self, name: str, credentials: dict[str, str]) -> None:
        provider = load_provider(name)
        provider.check_credentials(Credentials(kv=credentials))

    def load_available(self, language: str | None = None, package_manager: str | None = None) -> list[str]:
        tech_stack_provided = all([language, package_manager])
        
        names = []
        for provider in load_all_providers().values():
            if provider.requires_auth() and not has_secrets(provider.credential_keys):
                continue
            if provider.requires_tech_stack() and not tech_stack_provided:
                continue
            
            names.append(provider.name)
        
        return names


interface = ServiceProviders()
