from freeloader.pipeline.blocks.registry import BlockRegistry
from freeloader.projects.config import ConfigLoader
from freeloader.projects.state import StateManager
from freeloader.projects.usecases.init_project import InitProjectUseCases
from freeloader.projects.usecases.status import StatusUseCases
from freeloader.shared.paths import config_path, project_state_dir


class ProjectsFactory:
    def __init__(self, registry: BlockRegistry) -> None:
        self._registry = registry
        self._config_loader = ConfigLoader(config_path())

    @property
    def config_loader(self) -> ConfigLoader:
        return self._config_loader

    def init_usecases(self) -> InitProjectUseCases:
        return InitProjectUseCases(self._registry)

    def status_usecases(self, project_name: str) -> StatusUseCases:
        state_mgr = StateManager(project_name, project_state_dir(project_name))
        return StatusUseCases(state_mgr)
