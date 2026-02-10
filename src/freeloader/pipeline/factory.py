from pathlib import Path

from freeloader.blocks.models import RunnerType
from freeloader.blocks.registry import BlockRegistry
from freeloader.credentials.vault import SecretVault
from freeloader.pipeline.dag import DAGResolver
from freeloader.pipeline.orchestrator import Orchestrator
from freeloader.pipeline.runners import RunnerRegistry
from freeloader.pipeline.runners.api import APIRunner
from freeloader.pipeline.runners.generator import GeneratorRunner
from freeloader.pipeline.runners.terraform import TerraformRunner
from freeloader.pipeline.usecases.apply import ApplyUseCases
from freeloader.pipeline.usecases.generate import GenerateUseCases
from freeloader.projects.config import ConfigLoader
from freeloader.projects.state import StateManager
from freeloader.shared.paths import project_state_dir, project_tf_dir


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
        state_mgr = StateManager(project_name, project_state_dir(project_name))

        block_dirs = {
            c.block.name: self._registry.get_block_dir(c.block.name)
            for c in self._registry.list_blocks()
        }

        tf_dir = project_tf_dir(project_name)
        tf_dir.mkdir(parents=True, exist_ok=True)

        secrets_dict = {key: self._vault.get(
            key) for key in self._vault.list()}

        runner_registry = RunnerRegistry()
        runner_registry.register(
            RunnerType.terraform, TerraformRunner(tf_dir, self._vault, block_dirs))
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
        )
        return ApplyUseCases(orchestrator)

    def generate_usecases(self, output_dir: Path) -> GenerateUseCases:
        return GenerateUseCases(self._registry, output_dir)
