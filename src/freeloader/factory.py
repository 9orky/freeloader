from functools import cached_property

from freeloader.credentials.factory import CredentialsFactory
from freeloader.hosts.factory import HostsFactory
from freeloader.pipeline.blocks.registry import BlockRegistry
from freeloader.pipeline.factory import PipelineFactory
from freeloader.projects.factory import ProjectsFactory
from freeloader.shared.paths import blocks_dir, bundled_blocks_dir, ensure_home


class Factory:
    def __init__(self, passphrase: str | None = None) -> None:
        ensure_home()
        self._passphrase = passphrase

    @cached_property
    def registry(self) -> BlockRegistry:
        return BlockRegistry(blocks_dir(), bundled_blocks_dir())

    @cached_property
    def projects(self) -> ProjectsFactory:
        return ProjectsFactory(self.registry)

    @cached_property
    def credentials(self) -> CredentialsFactory:
        return CredentialsFactory(
            self._passphrase,
            self.registry,
            self.projects.config_loader,
        )

    @cached_property
    def hosts(self) -> HostsFactory:
        return HostsFactory()

    @cached_property
    def pipeline(self) -> PipelineFactory:
        return PipelineFactory(
            self.registry,
            self.credentials.vault(),
            self.projects.config_loader,
        )
