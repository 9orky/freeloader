from pathlib import Path

from freeloader.pipeline.blocks.models import RunnerType
from freeloader.pipeline.blocks.registry import BlockRegistry
from freeloader.credentials.vault import SecretVault
from freeloader.pipeline.dag import DAGResolver
from freeloader.pipeline.orchestrator import Orchestrator, Preflight
from freeloader.pipeline.progress import ProgressTracker
from freeloader.pipeline.runners import RunnerRegistry
from freeloader.pipeline.runners.api import APIRunner
from freeloader.pipeline.runners.generator import GeneratorRunner
from freeloader.pipeline.runners.terraform import TerraformRunner
from freeloader.pipeline.usecases.apply import ApplyUseCases
from freeloader.pipeline.usecases.blocks import BlockUseCases
from freeloader.pipeline.usecases.generate import GenerateUseCases
from freeloader.projects.config import ConfigLoader
from freeloader.projects.state import StateManager
from freeloader.shared.paths import project_state_dir, project_resource_dir


class PipelineFactory:
    def __init__(
        self,
        registry: BlockRegistry,
        vault: SecretVault,
        config_loader: ConfigLoader,
    ) -> None:
        self._registry = registry
        self._vault = vault
        self._config_loader = config_loader

    def apply_usecases(self, project_name: str) -> ApplyUseCases:
        config = self._config_loader.load()
        state_dir = project_state_dir(project_name)
        state_mgr = StateManager(project_name, state_dir)
        progress_tracker = ProgressTracker(state_dir)

        block_dirs = {
            c.block.name: self._registry.get_block_dir(c.block.name)
            for c in self._registry.list_blocks()
        }

        resource_dir = project_resource_dir(project_name)
        resource_dir.mkdir(parents=True, exist_ok=True)

        secrets_dict = {key: self._vault.get(
            key) for key in self._vault.list()}

        runner_registry = RunnerRegistry()
        runner_registry.register(
            RunnerType.terraform, TerraformRunner(resource_dir, self._vault, self._registry))
        runner_registry.register(
            RunnerType.generator, GeneratorRunner(Path.cwd(), block_dirs))
        runner_registry.register(
            RunnerType.api, APIRunner(block_dirs, secrets_dict))

        orchestrator = Orchestrator(
            dag_resolver=DAGResolver(),
            runner_registry=runner_registry,
            state_manager=state_mgr,
            vault=self._vault,
            config=config,
            block_registry=self._registry,
            progress_tracker=progress_tracker,
        )
        return ApplyUseCases(orchestrator)

    def generate_usecases(self, output_dir: Path) -> GenerateUseCases:
        preflight = Preflight(DAGResolver(), self._registry, self._vault)
        return GenerateUseCases(preflight, self._registry, output_dir)

    def block_usecases(self) -> BlockUseCases:
        return BlockUseCases(self._registry)
