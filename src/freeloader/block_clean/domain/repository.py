from abc import ABC, abstractmethod
from pathlib import Path

from .entity import Block, ProvisionedResource
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


class ResourceRepository(ABC):
    """Storage contract for managing block provisioning workspaces.

    Each `ProvisionedResource` is identified by its `BlockId`. The infrastructure
    implementation (`FileSystemResourceRepository`) owns the folder-path mapping;
    the application layer works exclusively with `ProvisionedResource` entities.
    """

    @abstractmethod
    def create(self, block_id: BlockId) -> ProvisionedResource:
        """Register a new workspace for `block_id` (creates backing storage)."""
        ...

    @abstractmethod
    def get(self, block_id: BlockId) -> ProvisionedResource | None:
        """Return the resource for `block_id`, or None if it does not exist."""
        ...

    @abstractmethod
    def remove(self, block_id: BlockId) -> None:
        """Destroy the workspace for `block_id` (deletes backing storage)."""
        ...

    @abstractmethod
    def list_all(self) -> list[ProvisionedResource]:
        """Return all currently registered resources."""
        ...
