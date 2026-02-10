from typing import TYPE_CHECKING, Any, Callable

from freeloader.pipeline.dag import DAGResolver, ResolvedBlock
from freeloader.pipeline.orchestrator._executor import BlockResult, PipelineExecutor
from freeloader.pipeline.orchestrator._preflight import Preflight
from freeloader.pipeline.orchestrator._resumption import ResumptionManager
from freeloader.pipeline.progress import ProgressTracker
from freeloader.projects.models import ProjectManifest

if TYPE_CHECKING:
    from freeloader.blocks.registry import BlockRegistry
    from freeloader.credentials.vault import SecretVault
    from freeloader.pipeline.runners import RunnerRegistry
    from freeloader.projects.config import GlobalConfig
    from freeloader.projects.state import StateManager


class Orchestrator:
    def __init__(
        self,
        dag_resolver: DAGResolver,
        runner_registry: "RunnerRegistry",
        state_manager: "StateManager",
        vault: "SecretVault",
        config: "GlobalConfig",
        block_registry: "BlockRegistry",
        progress_tracker: ProgressTracker,
    ) -> None:
        self._config = config
        self._preflight = Preflight(dag_resolver, block_registry, vault)
        self._executor = PipelineExecutor(
            runner_registry,
            state_manager,
            ResumptionManager(progress_tracker, state_manager),
        )

    def resolve(self, manifest: ProjectManifest) -> list[ResolvedBlock]:
        return self._preflight.resolve(manifest)

    def plan(
        self,
        manifest: ProjectManifest,
        *,
        on_block: Callable[[str, str], None] | None = None,
    ) -> list[tuple[str, str]]:
        self._preflight.check_secrets(manifest)
        resolved = self._preflight.resolve(manifest)
        return self._executor.plan(resolved, on_block=on_block)

    def apply(
        self,
        manifest: ProjectManifest,
        *,
        on_plan: Callable[[str, str], None] | None = None,
        on_apply: Callable[[str, dict[str, Any]], None] | None = None,
        on_skip: Callable[[str], None] | None = None,
    ) -> list[BlockResult]:
        self._preflight.check_secrets(manifest)
        resolved = self._preflight.resolve(manifest)
        return self._executor.apply(
            resolved, manifest,
            on_plan=on_plan, on_apply=on_apply, on_skip=on_skip,
        )

    def destroy(
        self,
        manifest: ProjectManifest,
        *,
        on_block: Callable[[str], None] | None = None,
    ) -> None:
        resolved = self._preflight.resolve(manifest)
        self._executor.destroy(resolved, manifest, on_block=on_block)
