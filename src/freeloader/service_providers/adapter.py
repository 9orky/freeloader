from ..secret import interface

def check_if_provider_has_credentials(provider_name: str, key: str) -> bool:
    return interface.has_secret(provider_name, key)