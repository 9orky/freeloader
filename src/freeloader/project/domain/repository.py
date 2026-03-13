import abc
from collections.abc import Iterator
from pathlib import Path

from freeloader.shared.block import BlockDestroyEvent, BlockProvisionEvent, BlockRef
from freeloader.shared.types import ConfigValue

from .entity import Manifest, TechStack


class ManifestRepository(abc.ABC):
    @abc.abstractmethod
    def manifest_exists(self, folder: Path) -> bool: ...

    @abc.abstractmethod
    def load(self, folder: Path) -> Manifest: ...

    @abc.abstractmethod
    def save(
        self,
        name: str,
        folder: Path,
        tech_stack: TechStack,
        block_configs: dict[str, dict[str, ConfigValue]],
    ) -> None: ...

    @abc.abstractmethod
    def delete(self, folder: Path) -> None: ...

    @abc.abstractmethod
    def resources_folder(self, folder: Path) -> Path: ...


class TechStackDetector(abc.ABC):
    @abc.abstractmethod
    def detect(self, folder: Path) -> TechStack | None: ...


class BlockGateway(abc.ABC):
    @abc.abstractmethod
    def get_manifest_configs(
        self,
        project_root: Path,
        tech_stack: TechStack,
        full_manifest: bool,
        project_name: str | None,
    ) -> dict[str, dict[str, ConfigValue]]: ...

    @abc.abstractmethod
    def provision(
        self,
        project_root: Path,
        resources_root: Path,
        block_refs: list[BlockRef],
    ) -> None: ...

    @abc.abstractmethod
    def provision_events(
        self,
        project_root: Path,
        resources_root: Path,
        block_refs: list[BlockRef],
    ) -> Iterator[BlockProvisionEvent]: ...

    @abc.abstractmethod
    def destroy(
        self,
        project_root: Path,
        resources_root: Path,
        block_refs: list[BlockRef],
    ) -> None: ...

    @abc.abstractmethod
    def destroy_events(
        self,
        project_root: Path,
        resources_root: Path,
        block_refs: list[BlockRef],
    ) -> Iterator[BlockDestroyEvent]: ...
