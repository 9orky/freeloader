from ..secrets import has_secrets

from .registry import load_all_providers, load_provider
from .base import Credentials


class ServiceProviders:
    def find_all(self) -> list[dict[str, str | bool | list[str]]]:
        return [{
            "name": name, 
            "requires_auth": provider.requires_auth,
            "requires_tech_stack": provider.requires_tech_stack,
            "auth_keys": provider.auth_keys,
        } for name, provider in load_all_providers().items()]
    
    def get(self, name: str) -> dict[str, str | bool | list[str]]:
        provider = load_provider(name)
        
        return {
            "name": name,
            "requires_auth": provider.requires_auth,
            "requires_tech_stack": provider.requires_tech_stack,
            "auth_keys": provider.auth_keys,
        }
    
    def get_credential_keys(self, name: str) -> list[str]:
        provider = load_provider(name)
        return provider.auth_keys

    def authorize_provider(self, name: str, credentials: dict[str, str]) -> None:
        provider = load_provider(name)
        provider.check_credentials(Credentials(kv=credentials))

    def load_available(self, language: str | None = None, package_manager: str | None = None) -> list[str]:
        tech_stack_provided = all([language, package_manager])
        
        names = []
        for name, provider in load_all_providers().items():
            if provider.requires_auth and not has_secrets(provider.auth_keys):
                continue
            if provider.requires_tech_stack and not tech_stack_provided:
                continue
            
            names.append(name)
        
        return names


interface = ServiceProviders()
