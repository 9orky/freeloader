from freeloader.secrets.ports.interface import Secrets


def write_credentials(credentials: dict[str, str]) -> None:
    secrets = Secrets.for_default_namespace()
    for key, value in credentials.items():
        secrets.write_secret(key, value)
