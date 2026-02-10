from functools import cached_property

from freeloader.blocks.factory import BlocksFactory
from freeloader.credentials.factory import CredentialsFactory
from freeloader.hosts.factory import HostsFactory
from freeloader.pipeline.factory import PipelineFactory
from freeloader.projects.factory import ProjectsFactory
from freeloader.shared.paths import ensure_home


class Factory:
    def __init__(self, passphrase: str | None = None) -> None:
        ensure_home()
        self._passphrase = passphrase

    @cached_property
    def blocks(self) -> BlocksFactory:
        return BlocksFactory()

    @cached_property
    def projects(self) -> ProjectsFactory:
        return ProjectsFactory(self.blocks.registry)

    @cached_property
    def credentials(self) -> CredentialsFactory:
        return CredentialsFactory(
            self._passphrase,
            self.blocks.registry,
            self.projects.config_loader,
        )

    @cached_property
    def hosts(self) -> HostsFactory:
        return HostsFactory()

    @cached_property
    def pipeline(self) -> PipelineFactory:
        return PipelineFactory(
            self.blocks.registry,
            self.credentials.vault(),
            self.projects.config_loader,
        )
