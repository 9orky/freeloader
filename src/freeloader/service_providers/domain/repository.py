from __future__ import annotations

from abc import ABC, abstractmethod

from .billing import BillingReport
from .entity import ServiceProvider
from .support import DriverSupportReport
from .value_object import CredentialKey, Credentials, ProviderName


class ProviderCatalog(ABC):
    @abstractmethod
    def list_providers(self) -> list[ServiceProvider]: ...

    @abstractmethod
    def get_provider(self, name: ProviderName | str) -> ServiceProvider: ...

    @abstractmethod
    def get_driver(self, name: ProviderName | str) -> "ProviderDriver": ...


class ProviderDriver(ABC):
    provider: ServiceProvider

    @abstractmethod
    def check_local_support(self) -> DriverSupportReport: ...

    @abstractmethod
    def validate_credentials(self, credentials: Credentials) -> None: ...

    @abstractmethod
    def fetch_billing(self, credentials: Credentials) -> BillingReport: ...


class CredentialRepository(ABC):
    @abstractmethod
    def read_credentials(self, keys: list[CredentialKey]) -> Credentials: ...

    @abstractmethod
    def write_credentials(self, credentials: Credentials) -> None: ...
