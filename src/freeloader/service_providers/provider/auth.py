import abc
from typing import Protocol
from dataclasses import dataclass


@dataclass(frozen=True)
class Credentials:
    kv: dict[str, str]


class ObtainTokenStep(Protocol):
    action: str
    value: str


class ServiceProviderAuth(Protocol):
    auth_keys: list[str] | None = None
    requires_tech_stack: bool = False
    obtain_token_steps: list[ObtainTokenStep] = []

    @property
    def requires_auth(self) -> bool:
        return bool(self.auth_keys)


class ServiceProvider(abc.ABC, ServiceProviderAuth):
    obtain_token_steps: list[ObtainTokenStep] = []

    @abc.abstractmethod
    def check_credentials(self, credentials: Credentials):
        raise NotImplementedError

    def check_installation(self) -> None:
        pass


class ServiceProviderError(Exception):
    pass


class ServiceProviderAuthError(ServiceProviderError):
    pass


@dataclass(frozen=True)
class Input(ObtainTokenStep):
    value: str
    action: str = "input"


@dataclass(frozen=True)
class Info(ObtainTokenStep):
    value: str
    action: str = "info"


@dataclass(frozen=True)
class OpenURL(ObtainTokenStep):
    value: str
    action: str = "open_url"


def get_obtain_steps(provider_name: str) -> list[ObtainTokenStep]:
    from .registry import load_provider

    return load_provider(provider_name).obtain_token_steps
