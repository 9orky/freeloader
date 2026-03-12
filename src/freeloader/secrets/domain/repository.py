import abc

from ..domain.entity import Secret
from ..domain.value_object import Password


class SecretRepository(abc.ABC):
    @abc.abstractmethod
    def get(self, key: str, namespace: str | None = None) -> Secret:
        raise NotImplementedError

    @abc.abstractmethod
    def store(self, key: str, value: str, namespace: str | None = None) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def store_many(self, values: dict[str, str], namespace: str | None = None) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def find(self, namespace: str | None = None) -> list[Secret]:
        raise NotImplementedError

    @abc.abstractmethod
    def delete(self, key: str, namespace: str | None = None) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def has(self, key: str, namespace: str | None = None) -> bool:
        raise NotImplementedError


class SessionRepository(abc.ABC):
    @abc.abstractmethod
    def get_password(self) -> Password:
        raise NotImplementedError

    @abc.abstractmethod
    def save_password(self, password: Password) -> None:
        raise NotImplementedError
