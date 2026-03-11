from freeloader.secrets.ports.interface import Secrets


def read_credentials(names: list[str]) -> dict[str, str]:
    if not names:
        return {}

    secrets = Secrets.for_default_namespace()
    return secrets.read_secrets(names)


def write_credentials(credentials: dict[str, str]) -> None:
    secrets = Secrets.for_default_namespace()
    secrets.write_secrets(credentials)
