import abc
from typing import Protocol
from dataclasses import dataclass


@dataclass(frozen=True)
class Credentials:
    kv: dict[str, str]


class ServiceProviderProtocol(Protocol):
    auth_keys: list[str]
    requires_auth: bool
    requires_tech_stack: bool = False


class ServiceProvider(abc.ABC, ServiceProviderProtocol):
    @abc.abstractmethod
    def check_credentials(self, credentials: Credentials):
        raise NotImplementedError
    
    def check_installation(self) -> None:
        pass
    

class ServiceProviderError(Exception):
    pass


class ServiceProviderAuthError(ServiceProviderError):
    pass
