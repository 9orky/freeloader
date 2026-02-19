import abc
import dataclasses
from .adapter import check_if_provider_has_credentials

@dataclasses.dataclass(frozen=True)
class Credentials:
    kv: dict[str, str]


class ServiceProvider(abc.ABC):
    @property
    @abc.abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def credential_keys(self) -> list[str]:
        raise NotImplementedError

    @abc.abstractmethod
    def check_credentials(self, credentials: Credentials):
        raise NotImplementedError

    def is_installed(self) -> bool:
        for key in self.credential_keys:
            if check_if_provider_has_credentials(self.name, key):
                return True
        return False