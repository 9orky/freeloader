from abc import ABC, abstractmethod
from pathlib import Path

from .entity import Block
from .value_object import BlockId


class SecretsReader(ABC):
    @abstractmethod
    def has_secrets(self, secret_names: list[str]) -> bool: ...

    @abstractmethod
    def read(self, secret_names: list[str]) -> dict[str, str]: ...


class BlockRepository(ABC):
    """Storage contract for discovering and loading block definitions."""

    @abstractmethod
    def load_all(self) -> dict[str, Block]: ...

    @abstractmethod
    def load_by_ids(self, block_ids: list[BlockId]) -> dict[str, Block]: ...

    @abstractmethod
    def dump_assets(self, block_id: BlockId, target: Path) -> None:
        """Copy the Terraform source files for `block_id` into `target`."""
        ...
