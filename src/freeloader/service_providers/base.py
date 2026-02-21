import abc
import dataclasses


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
    
    def requires_auth(self) -> bool:
        return bool(self.credential_keys)
    
    def requires_tech_stack(self) -> bool:
        return False
