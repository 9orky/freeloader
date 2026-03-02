from abc import ABC, abstractmethod

from freeloader.shared.types import ConfigValue


class BlockId(str):
    def __new__(cls, value: str):
        if "." not in value:
            raise ValueError(
                f"Invalid block id '{value}', expected format 'provider.block'")
        return str.__new__(cls, value)

    @property
    def sub_path(self) -> str:
        return f"{self.provider}/{self.block}"

    @property
    def provider(self) -> str:
        return self.split(".")[0]

    @property
    def block(self) -> str:
        return self.split(".")[1]


class SecretsReader(ABC):
    @abstractmethod
    def has_secrets(self, secret_names: list[str]) -> bool: ...

    @abstractmethod
    def read(self, secret_names: list[str]) -> dict[str, str]: ...
